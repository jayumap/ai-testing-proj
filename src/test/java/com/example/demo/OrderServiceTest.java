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

    @Test
    void shouldCalculateDiscountedTotalWithFractionalDiscount() {
        assertEquals(
                87.5,
                orderService.calculateDiscountedTotal(100.0, 12.5),
                0.0001
        );
    }

    @Test
    void shouldCalculateDiscountedTotalWithDecimalPriceAndDiscount() {
        assertEquals(
                66.663333,
                orderService.calculateDiscountedTotal(99.99, 33.33),
                0.0001
        );
    }

    @Test
    void shouldCalculateDiscountedTotalWithSmallDiscount() {
        assertEquals(
                999000.0,
                orderService.calculateDiscountedTotal(1000000.0, 0.1),
                0.0001
        );
    }

    @Test
    void shouldCalculateDiscountedTotalWithParenthesizedDiscountExpression() {
        assertEquals(
                80.0,
                orderService.calculateDiscountedTotal(100.0, 20.0),
                0.0001
        );
    }

    @Test
    void shouldCalculateDiscountedTotalWithIntegerDiscountPercent() {
        assertEquals(
                75.0,
                orderService.calculateDiscountedTotal(100.0, 25),
                0.0001
        );
    }

    @Test
    void shouldCalculateDiscountedTotalWithLargePriceAndDiscount() {
        assertEquals(
                500000.0,
                orderService.calculateDiscountedTotal(1000000.0, 50.0),
                0.0001
        );
    }

    @Test
    void shouldCalculateDiscountedTotalWithMaximumDiscountForDecimalPrice() {
        assertEquals(
                0.0,
                orderService.calculateDiscountedTotal(99.99, 100.0),
                0.0001
        );
    }

    @Test
    void shouldCalculateDiscountedTotalWithZeroPriceAndMaximumDiscount() {
        assertEquals(
                0.0,
                orderService.calculateDiscountedTotal(0.0, 100.0),
                0.0001
        );
    }

    @Test
    void shouldCalculateDiscountedTotalWithParenthesizedExpressionForDecimalPrice() {
        assertEquals(
                74.9925,
                orderService.calculateDiscountedTotal(99.99, 25.0),
                0.0001
        );
    }
}
