// User-editable what-if arithmetic, not the canonical backend savings model.
export function savingsPreview(hours: number, price: string, low: string, high: string) {
  if ([price,low,high].some(v => !v.trim())) return null;
  const p=Number(price), l=Number(low), h=Number(high);
  if (![hours,p,l,h].every(Number.isFinite) || hours<0 || p<0 || l<0 || h>100 || l>h) return null;
  const value=hours*p;
  if (!Number.isFinite(value)) return null;
  return {value,low:value*l/100,high:value*h/100};
}
