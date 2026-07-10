package com.smartlegal.common.constants;

public enum RiskLevel {
    CRITICAL("重大风险"),
    GENERAL("一般风险"),
    LOW("低风险");

    private final String description;

    RiskLevel(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}
