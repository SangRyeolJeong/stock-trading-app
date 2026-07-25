package com.moi.sim.dto;

public record SimulationRequest(
        long monthlyAmount,
        int years,
        double expectedReturnPercent
) {}
