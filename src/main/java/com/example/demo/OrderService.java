package com.example.demo;

import org.springframework.stereotype.Service;

@Service
public class OrderService {

    public double calculateTotal(double price, int quantity) {
        if (price < 0) {
            throw new IllegalArgumentException("Price cannot be negative");
        }

        if (quantity <= 0) {
            throw new IllegalArgumentException("Quantity must be greater than zero");
        }

        return price * quantity;
    }

    public String getOrderStatus(boolean paid, boolean shipped) {
        if (!paid) {
            // Order is waiting for payment.
            return "PENDING_PAYMENT";
        }

        if (!shipped) {
            // Order is getting processed.
            return "PROCESSING";
        }

        return "SHIPPED";
    }

    public boolean canCancelOrder(String status) {
        return "PENDING_PAYMENT".equals(status)
                || "PROCESSING".equals(status);
    }

    public double calculateDiscountedTotal(double price, double discountPercent) {
    if (price < 0) {
        throw new IllegalArgumentException("Price cannot be negative");
    }

    if (discountPercent < 0 || discountPercent > 100) {
        throw new IllegalArgumentException("Discount must be between 0 and 100");
    }

    double discountAmount = (price * discountPercent) / 100;
    return Math.round((price - discountAmount) * 10.0) / 10.0;
}

    public String getShippingCategory(double weight) {
    if (weight <= 0) {
        throw new IllegalArgumentException("Weight must be greater than zero");
    }

    if (weight <= 1.0) {
        return "LIGHT";
    }

    if (weight <= 5.0) {
        return "STANDARD";
    }

    return "HEAVY";
}
}
