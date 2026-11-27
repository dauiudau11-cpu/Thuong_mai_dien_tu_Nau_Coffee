"""Read-only refund projections using existing PaymentEvent and status history."""
def refund_context(order):
    payment = order.payment
    requested = payment.events.filter(event_key='refund_requested').first()
    cancelled = order.history.filter(to_state='CANCELLED').order_by('created_at','pk').first()
    confirmed = payment.events.filter(event_key='mock_refund').select_related('actor').first()
    return {'refund_requested_at': requested.created_at if requested else (cancelled.created_at if cancelled else None),
            'refund_confirmed_event': confirmed,
            'show_refund': payment.status in ('REFUND_PENDING','REFUNDED')}
