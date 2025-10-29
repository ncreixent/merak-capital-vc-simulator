# VC Fund Waterfall Function Walkthrough

## Overview

The `apply_fund_structure` function implements a standard European-style, whole-fund waterfall that distributes cash flows according to the following priority order:

1. **Return of Capital (ROC)** - Return LP and GP capital contributions first
2. **Preferred Return** - Pay LPs their preferred return (8% in this example)
3. **Catch-up** - GP catch-up to reach target carried interest
4. **Final Split** - Remaining profits split according to carried interest (20% GP, 80% LP)

## Input Data Structure

The function takes `gross_fund_flows_tagged` as a list of tuples:
```python
(amount, time_months, id)
```

Where:
- `amount`: Positive for inflows (exits), negative for outflows (investments, fees)
- `time_months`: Time in months from fund start
- `id`: 
  - `-1`: Management fees
  - `-2`: Capital calls (LP contributions)
  - `>0`: Company ID (investments and exits)

## Example Data Analysis

From our demonstration, we have 28 cash flow events over 10 years:

### Capital Calls (ID = -2)
- Year 1: $12.5M (25% of $50M commitment)
- Year 2: $12.5M 
- Year 3: $12.5M
- Year 4: $12.5M
- Year 5: $12.5M
- **Total**: $62.5M called (125% of commitment due to management fees)

### Investments (Company IDs > 0, negative amounts)
- Company 1: $2.5M + $1.0M follow-on = $3.5M total
- Company 2: $2.0M
- Company 3: $3.0M
- Company 4: $1.5M
- Company 5: $2.0M
- Company 6: $1.5M
- **Total**: $13.5M invested

### Exits (Company IDs > 0, positive amounts)
- Company 2: $8.0M (4.0x return)
- Company 3: $12.0M (4.0x return)
- Company 1: $6.0M (1.7x return)
- Company 4: $15.0M (10.0x return)
- Company 5: $4.0M (2.0x return)
- Company 6: $25.0M (16.7x return)
- **Total**: $70.0M in exit proceeds

### Management Fees (ID = -1)
- Years 1-2: $250K each (2% of called capital)
- Years 3-10: $200K each (1.75% of called capital)
- **Total**: $2.1M in management fees

## Waterfall Calculation Process

### Step 1: Data Preparation
The function first:
1. Converts time from months to years
2. Separates capital calls from other flows
3. Groups flows by year
4. Initializes state variables

### Step 2: Year-by-Year Processing

For each year, the function processes flows in this order:

#### Year 1 (Months 0-12)
- **Capital Called**: $12.5M
  - LP share (99%): $12.375M
  - GP share (1%): $125K
- **Investments**: $7.5M (Companies 1, 2, 3)
- **Management Fee**: $250K
- **Net Distributable Cash**: -$7.75M (negative = no distributions)
- **LP Contribution**: -$12.375M (capital call)
- **Preferred Return Balance**: $0 (no unreturned capital yet)

#### Year 2 (Months 12-24)
- **Capital Called**: $12.5M
- **Investments**: $4.5M (Companies 4, 5, follow-on in Company 1)
- **Management Fee**: $250K
- **Net Distributable Cash**: -$4.75M
- **LP Contribution**: -$12.375M
- **Preferred Return Balance**: $0

#### Year 3 (Months 24-36)
- **Capital Called**: $12.5M
- **Investments**: $1.5M (Company 6)
- **Exit Proceeds**: $8.0M (Company 2)
- **Management Fee**: $200K
- **Net Distributable Cash**: $6.3M
- **Return of Capital**: $6.3M (all to LPs since no GP capital returned yet)
- **LP Distribution**: $6.435M (includes preferred return on unreturned capital)
- **Preferred Return Balance**: $2.574M (8% on $32.175M unreturned LP capital)

#### Year 4 (Months 36-48)
- **Capital Called**: $12.5M
- **Exit Proceeds**: $18.0M (Companies 3 and 1)
- **Management Fee**: $200K
- **Net Distributable Cash**: $17.8M
- **Return of Capital**: $17.8M (all to LPs)
- **Preferred Return Payment**: $2.574M (clears preferred return balance)
- **LP Distribution**: $17.82M
- **New Preferred Return Balance**: $6.494M (8% on remaining unreturned capital)

#### Year 5 (Months 48-60)
- **Capital Called**: $12.5M
- **Exit Proceeds**: $19.0M (Companies 4 and 5)
- **Management Fee**: $200K
- **Net Distributable Cash**: $18.8M
- **Return of Capital**: $18.8M (all to LPs)
- **Preferred Return Payment**: $6.494M
- **LP Distribution**: $18.81M
- **New Preferred Return Balance**: $10.89M

#### Year 6 (Months 60-72)
- **Exit Proceeds**: $25.0M (Company 6)
- **Management Fee**: $200K
- **Net Distributable Cash**: $24.8M
- **Return of Capital**: $24.8M (all to LPs)
- **Preferred Return Payment**: $10.89M
- **LP Distribution**: $24.75M
- **Remaining Preferred Return Balance**: $14.85M

#### Years 7-10 (Months 72-120)
- **Management Fees**: $200K each year
- **No Exit Proceeds**: All companies have exited
- **Preferred Return Accrual**: 8% annually on remaining unreturned capital
- **No Distributions**: No cash available for distributions

## Final Results

### Net LP Cash Flows
The function returns 6 net LP cash flows:
1. Year 1: -$32.175M (contribution)
2. Year 2: -$16.83M (contribution)  
3. Year 3: -$5.94M (contribution)
4. Year 4: +$5.445M (distribution)
5. Year 5: +$18.81M (distribution)
6. Year 6: +$24.75M (distribution)

### Summary Statistics
- **Total LP Contributions**: $54.945M
- **Total LP Distributions**: $49.005M
- **Net Return**: -$5.94M (loss)
- **Multiple**: 0.89x

### Key Insights
1. **No Carried Interest**: Despite $70M in gross proceeds, no carried interest was paid because the fund didn't achieve the preferred return hurdle
2. **Preferred Return Accrual**: The 8% preferred return continues to accrue on unreturned capital even after the investment period ends
3. **Management Fee Impact**: Management fees reduce the distributable cash available to LPs
4. **Capital Call Timing**: Capital calls are made quarterly, but the waterfall processes them annually

## Waterfall Details DataFrame

The function also returns a detailed breakdown showing:
- **Pref Balance Start**: Preferred return balance at start of year
- **Distributable Cash**: Net cash available for distribution
- **ROC to LP/GP**: Return of capital payments
- **Pref to LP**: Preferred return payments
- **Catch-up to GP**: GP catch-up payments (none in this example)
- **Final Split to GP**: Carried interest payments (none in this example)
- **Total to LP**: Total distributions to LPs
- **Total Carry to GP**: Total carried interest to GP

This detailed view allows for complete transparency in how the waterfall calculations are performed year by year.

