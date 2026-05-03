"""Chat: список диалогов, открыть чат по объявлению, тред + отправка сообщения.

HTMX-полинг для свежих сообщений: /chat/<id>/messages_partial каждые 3 сек.
"""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.entrypoints.http.deps.auth import current_user
from app.entrypoints.http.deps.messaging import messaging_repo
from app.entrypoints.http.deps.listings import listing_repo
from app.entrypoints.http.deps.users import user_repo
from app.entrypoints.http.templates_setup import templates

from app.modules.messaging import (
    open_or_get_conversation, send_message, get_thread,
    ConversationNotFound, NotAConversationParticipant, ListingNotMessageable,
)
from app.modules.listings import ListingNotFound, get_listing


router = APIRouter()


@router.post("/{lang}/l/{listing_id}/contact")
async def contact_seller(
    lang: str,
    listing_id: int,
    request: Request,
    user=Depends(current_user),
    msg_repo=Depends(messaging_repo),
    listings=Depends(listing_repo),
):
    try:
        conv = await open_or_get_conversation(
            msg_repo, listings, listing_id=listing_id, buyer_id=user.id
        )
    except ListingNotMessageable:
        raise HTTPException(400, "это объявление импортировано — пиши через Telegram")
    except ListingNotFound:
        raise HTTPException(404, "listing not found")
    except NotAConversationParticipant as e:
        raise HTTPException(400, str(e))

    return RedirectResponse(f"/{lang}/chat/{conv.id}", status_code=303)


@router.get("/{lang}/chat")
async def conversations_list(
    lang: str,
    request: Request,
    user=Depends(current_user),
    msg_repo=Depends(messaging_repo),
    listings=Depends(listing_repo),
):
    convs = await msg_repo.list_user_conversations(user.id)
    # подгружаем listings для отображения
    items = []
    for c in convs:
        try:
            listing = await get_listing(listings, c.listing_id)
        except ListingNotFound:
            continue
        items.append({"conv": c, "listing": listing})
    return templates.TemplateResponse(
        "chat_list.html",
        {"request": request, "lang": lang, "user": user, "items": items},
    )


@router.get("/{lang}/chat/{conv_id}")
async def chat_thread(
    lang: str,
    conv_id: int,
    request: Request,
    user=Depends(current_user),
    msg_repo=Depends(messaging_repo),
    listings=Depends(listing_repo),
    users=Depends(user_repo),
):
    try:
        conv, messages = await get_thread(msg_repo, conversation_id=conv_id, user_id=user.id)
    except ConversationNotFound:
        raise HTTPException(404)
    except NotAConversationParticipant:
        raise HTTPException(403)

    listing = await get_listing(listings, conv.listing_id)
    other_id = conv.seller_id if conv.buyer_id == user.id else conv.buyer_id
    other = await users.get(other_id)

    return templates.TemplateResponse(
        "chat_thread.html",
        {
            "request": request, "lang": lang, "user": user,
            "conv": conv, "messages": messages, "listing": listing, "other": other,
        },
    )


@router.post("/{lang}/chat/{conv_id}/send")
async def chat_send(
    lang: str,
    conv_id: int,
    request: Request,
    text: str = Form(...),
    user=Depends(current_user),
    msg_repo=Depends(messaging_repo),
):
    try:
        await send_message(msg_repo, conversation_id=conv_id, sender_id=user.id, text=text)
    except (ConversationNotFound, NotAConversationParticipant, ValueError) as e:
        raise HTTPException(400, str(e))
    return RedirectResponse(f"/{lang}/chat/{conv_id}", status_code=303)


@router.get("/{lang}/chat/{conv_id}/messages_partial")
async def chat_messages_partial(
    lang: str,
    conv_id: int,
    request: Request,
    user=Depends(current_user),
    msg_repo=Depends(messaging_repo),
):
    """HTMX-полинг: возвращает только список сообщений, для авто-обновления."""
    try:
        conv, messages = await get_thread(msg_repo, conversation_id=conv_id, user_id=user.id)
    except (ConversationNotFound, NotAConversationParticipant):
        raise HTTPException(403)
    return templates.TemplateResponse(
        "_chat_messages.html",
        {"request": request, "lang": lang, "user": user, "messages": messages, "conv": conv},
    )
