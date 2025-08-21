from handlers.registration import (
    handle_registration_callback,
    handle_cancel_registration,
    handle_confirm_registration,
    handle_edit_registration
)
from handlers.admin import (
    handle_admin_start,
    handle_admin_stats,
    handle_admin_events,
    handle_admin_approvals,
    handle_registration_review,
    handle_approve_registration,
    handle_reject_registration,
    handle_view_receipt,
    handle_admin_excel,
    handle_generate_excel,
    handle_admin_back
)
from utils.helpers import log_activity
import logging

logger = logging.getLogger(__name__)

async def handle_callback_query(event, client):
    """Main callback query handler"""
    try:
        data = event.data.decode('utf-8')
        telegram_id = event.chat_id
        
        # Log callback action
        await log_activity(telegram_id, "callback_query", data)
        
        # Registration callbacks
        if data.startswith('start_registration_'):
            event_id = data.replace('start_registration_', '')
            await handle_registration_callback(event, client, event_id)
            
        elif data == 'cancel_registration':
            await handle_cancel_registration(event, client)
            
        elif data == 'confirm_registration':
            await handle_confirm_registration(event, client)
            
        elif data == 'edit_registration':
            await handle_edit_registration(event, client)
        
        # Admin callbacks
        elif data == 'admin_start' or data == 'admin_back':
            await handle_admin_back(event, client)
            
        elif data == 'admin_stats':
            await handle_admin_stats(event, client)
            
        elif data == 'admin_events':
            await handle_admin_events(event, client)
            
        elif data == 'admin_approvals':
            await handle_admin_approvals(event, client)
            
        elif data.startswith('admin_review_'):
            registration_id = data.replace('admin_review_', '')
            await handle_registration_review(event, client, int(registration_id))
            
        elif data.startswith('approve_'):
            registration_id = data.replace('approve_', '')
            await handle_approve_registration(event, client, int(registration_id))
            
        elif data.startswith('reject_'):
            registration_id = data.replace('reject_', '')
            await handle_reject_registration(event, client, int(registration_id))
            
        elif data.startswith('view_receipt_'):
            registration_id = data.replace('view_receipt_', '')
            await handle_view_receipt(event, client, int(registration_id))
            
        elif data == 'admin_excel':
            await handle_admin_excel(event, client)
            
        elif data.startswith('excel_'):
            event_id = data.replace('excel_', '')
            await handle_generate_excel(event, client, int(event_id))
        
        # Event management callbacks (to be implemented)
        elif data.startswith('admin_event_'):
            event_id = data.replace('admin_event_', '')
            await handle_event_detail(event, client, int(event_id))
            
        elif data == 'admin_create_event':
            await handle_create_event_start(event, client)
        
        else:
            logger.warning(f"Unhandled callback: {data}")
            await event.answer("❌ عملیات نامشخص.")
            
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        await event.answer("❌ خطایی رخ داد.")

async def handle_event_detail(event, client, event_id):
    """Handle event detail view (placeholder)"""
    # This would show event details and management options
    await event.answer("🔧 این بخش در حال توسعه است.")

async def handle_create_event_start(event, client):
    """Handle event creation start (placeholder)"""
    # This would start the event creation process
    await event.answer("🔧 ایجاد رویداد در حال توسعه است.")