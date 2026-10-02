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
            return "PENDING_PAYMENT";
        }

        if (!shipped) {
            return "PROCESSING";
        }

        return "SHIPPED";
    }

    public boolean canCancelOrder(String status) {
        return "PENDING_PAYMENT".equals(status)
                || "PROCESSING".equals(status);
    }
}