package com.example.demo;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class OrderServiceTest {

    private final OrderService orderService = new OrderService();

    @Test
    void shouldCalculateTotal() {
        assertEquals(500.0, orderService.calculateTotal(100.0, 5));
    }

    @Test
    void shouldRejectNegativePrice() {
        assertThrows(
                IllegalArgumentException.class,
                () -> orderService.calculateTotal(-100.0, 2)
        );
    }

    @Test
    void shouldReturnPendingPaymentWhenOrderIsNotPaid() {
        assertEquals(
                "PENDING_PAYMENT",
                orderService.getOrderStatus(false, false)
        );
    }

    @Test
    void shouldReturnProcessingWhenPaidButNotShipped() {
        assertEquals(
                "PROCESSING",
                orderService.getOrderStatus(true, false)
        );
    }

    @Test
    void shouldReturnShippedWhenPaidAndShipped() {
        assertEquals(
                "SHIPPED",
                orderService.getOrderStatus(true, true)
        );
    }

    @Test
    void shouldAllowCancellationForPendingPayment() {
        assertTrue(orderService.canCancelOrder("PENDING_PAYMENT"));
    }

    @Test
    void shouldNotAllowCancellationForShippedOrder() {
        assertFalse(orderService.canCancelOrder("SHIPPED"));
    }
}