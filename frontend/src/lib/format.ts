/** "120–200 BGN", "150 BGN", or null when no budget is set. */
export function budgetLabel(t: {
  budget_min?: number | null;
  budget_max?: number | null;
}): string | null {
  if (t.budget_min == null && t.budget_max == null) return null;
  if (t.budget_min != null && t.budget_max != null) return `${t.budget_min}–${t.budget_max} BGN`;
  return `${t.budget_min ?? t.budget_max} BGN`;
}
