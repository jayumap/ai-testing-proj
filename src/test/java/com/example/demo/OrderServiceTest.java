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

    @Test
    void shouldCalculateDiscountedTotal() {
        assertEquals(
                90.0,
                orderService.calculateDiscountedTotal(100.0, 10.0),
                0.0001
        );
    }

    @Test
    void shouldReturnOriginalPriceWhenDiscountIsZero() {
        assertEquals(
                100.0,
                orderService.calculateDiscountedTotal(100.0, 0.0),
                0.0001
        );
    }

    @Test
    void shouldReturnZeroWhenDiscountIsOneHundredPercent() {
        assertEquals(
                0.0,
                orderService.calculateDiscountedTotal(100.0, 100.0),
                0.0001
        );
    }

    @Test
    void shouldReturnZeroWhenPriceIsZero() {
        assertEquals(
                0.0,
                orderService.calculateDiscountedTotal(0.0, 50.0),
                0.0001
        );
    }

    @Test
    void shouldRejectNegativePriceForDiscountedTotal() {
        assertThrows(
                IllegalArgumentException.class,
                () -> orderService.calculateDiscountedTotal(-10.0, 10.0)
        );
    }

    @Test
    void shouldRejectNegativeDiscountForDiscountedTotal() {
        assertThrows(
                IllegalArgumentException.class,
                () -> orderService.calculateDiscountedTotal(100.0, -1.0)
        );
    }

    @Test
    void shouldRejectDiscountGreaterThanOneHundredForDiscountedTotal() {
        assertThrows(
                IllegalArgumentException.class,
                () -> orderService.calculateDiscountedTotal(100.0, 101.0)
        );
    }
}
