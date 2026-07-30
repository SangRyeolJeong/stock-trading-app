export interface WholeShareOrderDraftInput {
  allocationKrw: number;
  priceUsd: number;
  usdKrwRate: number;
  feeRate?: number;
}

export interface WholeShareOrderDraft {
  quantity: number;
  unitPriceKrw: number;
  grossAmountKrw: number;
  feeAmountKrw: number;
  totalAmountKrw: number;
  remainingKrw: number;
}

export function calculateWholeShareOrderDraft(
  input: WholeShareOrderDraftInput,
): WholeShareOrderDraft {
  const allocationKrw = Math.max(0, input.allocationKrw);
  const priceUsd = Math.max(0, input.priceUsd);
  const usdKrwRate = Math.max(0, input.usdKrwRate);
  const feeRate = Math.max(0, input.feeRate ?? 0.001);
  const unitPriceKrw = priceUsd * usdKrwRate;
  const unitCostKrw = unitPriceKrw * (1 + feeRate);
  const quantity = unitCostKrw > 0
    ? Math.floor(allocationKrw / unitCostKrw)
    : 0;
  const grossAmountKrw = unitPriceKrw * quantity;
  const feeAmountKrw = grossAmountKrw * feeRate;
  const totalAmountKrw = grossAmountKrw + feeAmountKrw;

  return {
    quantity,
    unitPriceKrw,
    grossAmountKrw,
    feeAmountKrw,
    totalAmountKrw,
    remainingKrw: Math.max(0, allocationKrw - totalAmountKrw),
  };
}
