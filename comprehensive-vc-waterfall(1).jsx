import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import { TrendingDown, TrendingUp, Calendar, DollarSign, Users, Building, PieChart } from 'lucide-react';

const ComprehensiveVCWaterfall = () => {
  // Fund parameters
  const fundSize = 100;
  const preferredReturnRate = 8;
  const carryPercentage = 20;

  // Year-by-year LP distributions (contributions are negative, distributions are positive)
  const yearlyData = [
    {
      year: 'Year 0',
      contributions: -25,
      returnOfCapital: 0,
      preferredReturn: 0,
    },
    {
      year: 'Year 1',
      contributions: -30,
      returnOfCapital: 0,
      preferredReturn: 0,
    },
    {
      year: 'Year 2',
      contributions: -25,
      returnOfCapital: 0,
      preferredReturn: 0,
    },
    {
      year: 'Year 3',
      contributions: -20,
      returnOfCapital: 5,
      preferredReturn: 0,
    },
    {
      year: 'Year 4',
      contributions: 0,
      returnOfCapital: 15,
      preferredReturn: 0,
    },
    {
      year: 'Year 5',
      contributions: 0,
      returnOfCapital: 25,
      preferredReturn: 2,
    },
    {
      year: 'Year 6',
      contributions: 0,
      returnOfCapital: 30,
      preferredReturn: 4,
    },
    {
      year: 'Year 7',
      contributions: 0,
      returnOfCapital: 20,
      preferredReturn: 2,
    },
    {
      year: 'Year 8',
      contributions: 0,
      returnOfCapital: 5,
      preferredReturn: 0.4,
    },
    {
      year: 'Year 9',
      contributions: 0,
      returnOfCapital: 0,
      preferredReturn: 0,
    },
    {
      year: 'Year 10',
      contributions: 0,
      returnOfCapital: 0,
      preferredReturn: 0,
    }
  ];

  // Calculate LP totals
  const totalContributions = yearlyData.reduce((sum, item) => sum + Math.abs(item.contributions), 0);
  const lpReturnOfCapital = yearlyData.reduce((sum, item) => sum + item.returnOfCapital, 0);
  const lpPreferredReturn = yearlyData.reduce((sum, item) => sum + item.preferredReturn, 0);
  const totalLPDistributions = lpReturnOfCapital + lpPreferredReturn;

  // Calculate GP distributions with catch-up
  const profitsAfterHurdle = totalLPDistributions - totalContributions;
  
  // Calculate catch-up: GP receives 100% until they catch up to their carry %
  // Target: GP should have 20% of (Return of Capital + Preferred Return + Catch-up)
  const lpBeforeCatchup = lpReturnOfCapital + lpPreferredReturn;
  const catchupTarget = lpBeforeCatchup * (carryPercentage / (100 - carryPercentage));
  const gpCatchup = Math.min(profitsAfterHurdle, catchupTarget);
  
  // Remaining profits split 80/20
  const remainingProfits = Math.max(0, profitsAfterHurdle - gpCatchup);
  const lpCarriedInterest = remainingProfits * ((100 - carryPercentage) / 100);
  const gpCarriedInterest = remainingProfits * (carryPercentage / 100);
  
  const totalGPCarry = gpCatchup + gpCarriedInterest;
  
  // Add GP distributions to yearly data
  // Catch-up happens in Years 7-8, then remaining carry in Years 9-10
  const yearlyDataWithCarry = yearlyData.map((item, index) => {
    let lpCarry = 0;
    
    // Distribute LP's share of carry in later years
    if (index === 7) lpCarry = 3;
    if (index === 8) lpCarry = 8;
    if (index === 9) lpCarry = 15;
    if (index === 10) lpCarry = 25;
    
    return {
      ...item,
      carriedInterest: lpCarry,
    };
  });

  const totalLPDistributionsWithCarry = totalLPDistributions + lpCarriedInterest;
  const totalFundDistributions = totalLPDistributionsWithCarry + totalGPCarry;

  // Calculate cumulative for yearly data
  const enrichedYearlyData = (() => {
    let cumulative = 0;
    return yearlyDataWithCarry.map(item => {
      const netCashFlow = item.contributions + item.returnOfCapital + item.preferredReturn + item.carriedInterest;
      cumulative += netCashFlow;
      return {
        ...item,
        netCashFlow,
        cumulative
      };
    });
  })();

  // Fund-level waterfall data (GP/LP split)
  const fundWaterfallData = [
    {
      stage: 'Return of Capital',
      lp: lpReturnOfCapital,
      gp: 0,
      description: 'LPs receive invested capital back',
      color: '#3b82f6'
    },
    {
      stage: 'Preferred Return',
      lp: lpPreferredReturn,
      gp: 0,
      description: `LPs receive ${preferredReturnRate}% preferred return`,
      color: '#10b981'
    },
    {
      stage: 'GP Catch-up',
      lp: 0,
      gp: gpCatchup,
      description: `GP receives 100% until they reach ${carryPercentage}% of total`,
      color: '#f59e0b'
    },
    {
      stage: 'Carried Interest',
      lp: lpCarriedInterest,
      gp: gpCarriedInterest,
      description: `${100-carryPercentage}/${carryPercentage} split of remaining profits`,
      color: '#8b5cf6'
    }
  ];

  const totalLP = fundWaterfallData.reduce((sum, item) => sum + item.lp, 0);
  const totalGP = fundWaterfallData.reduce((sum, item) => sum + item.gp, 0);

  const FundTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 rounded-lg shadow-xl border-2 border-gray-200">
          <p className="font-bold text-gray-800 mb-2 text-lg">{data.stage}</p>
          <p className="text-sm text-gray-600 mb-2">{data.description}</p>
          <p className="text-blue-600 font-semibold">LP: ${data.lp.toFixed(1)}M</p>
          <p className="text-orange-600 font-semibold">GP: ${data.gp.toFixed(1)}M</p>
          <p className="text-gray-900 font-bold mt-2">Total: ${(data.lp + data.gp).toFixed(1)}M</p>
        </div>
      );
    }
    return null;
  };

  const YearlyTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 rounded-lg shadow-xl border-2 border-gray-200">
          <p className="font-bold text-gray-900 mb-2 text-lg">{label}</p>
          
          {data.contributions < 0 && (
            <div className="mb-2 pb-2 border-b border-gray-200">
              <p className="text-red-600 font-semibold">
                Capital Calls: ${Math.abs(data.contributions).toFixed(1)}M
              </p>
            </div>
          )}
          
          {(data.returnOfCapital > 0 || data.preferredReturn > 0 || data.carriedInterest > 0) && (
            <div className="mb-2 pb-2 border-b border-gray-200">
              <p className="text-sm font-semibold text-gray-700 mb-1">LP Distributions:</p>
              {data.returnOfCapital > 0 && (
                <p className="text-blue-600 text-sm">Return of Capital: ${data.returnOfCapital.toFixed(1)}M</p>
              )}
              {data.preferredReturn > 0 && (
                <p className="text-green-600 text-sm">Preferred Return: ${data.preferredReturn.toFixed(1)}M</p>
              )}
              {data.carriedInterest > 0 && (
                <p className="text-purple-600 text-sm">Carried Interest: ${data.carriedInterest.toFixed(1)}M</p>
              )}
            </div>
          )}
          
          <p className="font-bold text-gray-900">Net Cash Flow: ${data.netCashFlow.toFixed(1)}M</p>
          <p className="text-sm text-gray-600">Cumulative: ${data.cumulative.toFixed(1)}M</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-50 to-blue-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">VC Fund Waterfall Analysis</h1>
          <p className="text-lg text-gray-600">Complete Distribution & Cash Flow Overview</p>
        </div>

        {/* Top-Level Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-gray-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Fund Size</p>
                <p className="text-2xl font-bold text-gray-900">${fundSize}M</p>
              </div>
              <Building className="w-10 h-10 text-gray-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Distributions</p>
                <p className="text-2xl font-bold text-green-600">${totalFundDistributions.toFixed(1)}M</p>
              </div>
              <TrendingUp className="w-10 h-10 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">LP Returns</p>
                <p className="text-2xl font-bold text-blue-600">${totalLP.toFixed(1)}M</p>
              </div>
              <Users className="w-10 h-10 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-orange-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">GP Carry</p>
                <p className="text-2xl font-bold text-orange-600">${totalGP.toFixed(1)}M</p>
              </div>
              <DollarSign className="w-10 h-10 text-orange-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">MOIC</p>
                <p className="text-2xl font-bold text-purple-600">{(totalFundDistributions / fundSize).toFixed(2)}x</p>
              </div>
              <PieChart className="w-10 h-10 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Section 1: Fund-Level Distribution (GP/LP Split) */}
        <div className="bg-white rounded-lg shadow-xl p-6 mb-8">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Fund-Level Distribution Waterfall</h2>
            <p className="text-gray-600">Total distributions split between Limited Partners (LP) and General Partner (GP)</p>
          </div>
          
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={fundWaterfallData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="stage" tick={{ fill: '#4b5563', fontSize: 13 }} />
              <YAxis 
                label={{ value: 'Amount ($M)', angle: -90, position: 'insideLeft', fill: '#4b5563' }}
                tick={{ fill: '#4b5563' }}
              />
              <Tooltip content={<FundTooltip />} />
              <Legend />
              <Bar dataKey="lp" name="LP Distribution" stackId="a" fill="#3b82f6" />
              <Bar dataKey="gp" name="GP Distribution" stackId="a" fill="#f97316" />
            </BarChart>
          </ResponsiveContainer>

          {/* Fund-Level Summary Table */}
          <div className="mt-6 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200 bg-gray-50">
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">Stage</th>
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">Description</th>
                  <th className="text-right py-3 px-4 text-gray-700 font-semibold">LP Amount</th>
                  <th className="text-right py-3 px-4 text-gray-700 font-semibold">GP Amount</th>
                  <th className="text-right py-3 px-4 text-gray-700 font-semibold">Total</th>
                  <th className="text-right py-3 px-4 text-gray-700 font-semibold">% of Total</th>
                </tr>
              </thead>
              <tbody>
                {fundWaterfallData.map((item, index) => {
                  const total = item.lp + item.gp;
                  const percentage = (total / totalFundDistributions) * 100;
                  return (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{item.stage}</td>
                      <td className="py-3 px-4 text-gray-600 text-sm">{item.description}</td>
                      <td className="py-3 px-4 text-right text-blue-600 font-semibold">
                        ${item.lp.toFixed(1)}M
                      </td>
                      <td className="py-3 px-4 text-right text-orange-600 font-semibold">
                        ${item.gp.toFixed(1)}M
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-gray-900">
                        ${total.toFixed(1)}M
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600">
                        {percentage.toFixed(1)}%
                      </td>
                    </tr>
                  );
                })}
                <tr className="bg-gray-50 font-bold border-t-2 border-gray-300">
                  <td className="py-3 px-4" colSpan="2">Total Distribution</td>
                  <td className="py-3 px-4 text-right text-blue-600">${totalLP.toFixed(1)}M</td>
                  <td className="py-3 px-4 text-right text-orange-600">${totalGP.toFixed(1)}M</td>
                  <td className="py-3 px-4 text-right text-gray-900">${totalFundDistributions.toFixed(1)}M</td>
                  <td className="py-3 px-4 text-right text-gray-600">100.0%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 2: Year-by-Year LP Cash Flows */}
        <div className="bg-white rounded-lg shadow-xl p-6 mb-8">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Year-by-Year LP Cash Flows</h2>
            <p className="text-gray-600">Annual contributions (negative) and distributions (positive) to Limited Partners</p>
          </div>

          <ResponsiveContainer width="100%" height={450}>
            <BarChart data={enrichedYearlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="year" 
                tick={{ fill: '#4b5563', fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                label={{ value: 'LP Cash Flow ($M)', angle: -90, position: 'insideLeft', fill: '#4b5563' }}
                tick={{ fill: '#4b5563' }}
              />
              <Tooltip content={<YearlyTooltip />} />
              <Legend 
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="rect"
              />
              <ReferenceLine y={0} stroke="#000" strokeWidth={2} />
              
              {/* Negative bars for contributions */}
              <Bar 
                dataKey="contributions" 
                name="Capital Calls" 
                fill="#dc2626" 
                radius={[0, 0, 4, 4]}
              />
              
              {/* Positive bars for distributions */}
              <Bar 
                dataKey="returnOfCapital" 
                name="Return of Capital" 
                stackId="distributions"
                fill="#3b82f6" 
              />
              <Bar 
                dataKey="preferredReturn" 
                name="Preferred Return" 
                stackId="distributions"
                fill="#10b981" 
              />
              <Bar 
                dataKey="carriedInterest" 
                name="Carried Interest (LP Share)" 
                stackId="distributions"
                fill="#8b5cf6" 
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Detailed Year-by-Year Table */}
        <div className="bg-white rounded-lg shadow-xl p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Detailed LP Cash Flow Schedule</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-300 bg-gray-50">
                  <th className="text-left py-3 px-3 font-semibold text-gray-700">Period</th>
                  <th className="text-right py-3 px-3 font-semibold text-gray-700">Capital Calls</th>
                  <th className="text-right py-3 px-3 font-semibold text-gray-700">Return of Capital</th>
                  <th className="text-right py-3 px-3 font-semibold text-gray-700">Preferred Return</th>
                  <th className="text-right py-3 px-3 font-semibold text-gray-700">Carried Interest</th>
                  <th className="text-right py-3 px-3 font-semibold text-gray-700">Net Cash Flow</th>
                  <th className="text-right py-3 px-3 font-semibold text-gray-700">Cumulative</th>
                </tr>
              </thead>
              <tbody>
                {enrichedYearlyData.map((item, index) => (
                  <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-3 font-medium text-gray-900">{item.year}</td>
                    <td className="py-3 px-3 text-right text-red-600 font-semibold">
                      {item.contributions < 0 ? `($${Math.abs(item.contributions).toFixed(1)}M)` : '-'}
                    </td>
                    <td className="py-3 px-3 text-right text-blue-600">
                      {item.returnOfCapital > 0 ? `$${item.returnOfCapital.toFixed(1)}M` : '-'}
                    </td>
                    <td className="py-3 px-3 text-right text-green-600">
                      {item.preferredReturn > 0 ? `$${item.preferredReturn.toFixed(1)}M` : '-'}
                    </td>
                    <td className="py-3 px-3 text-right text-purple-600">
                      {item.carriedInterest > 0 ? `$${item.carriedInterest.toFixed(1)}M` : '-'}
                    </td>
                    <td className={`py-3 px-3 text-right font-semibold ${item.netCashFlow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {item.netCashFlow >= 0 ? `$${item.netCashFlow.toFixed(1)}M` : `($${Math.abs(item.netCashFlow).toFixed(1)}M)`}
                    </td>
                    <td className={`py-3 px-3 text-right font-bold ${item.cumulative >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                      {item.cumulative >= 0 ? `$${item.cumulative.toFixed(1)}M` : `($${Math.abs(item.cumulative).toFixed(1)}M)`}
                    </td>
                  </tr>
                ))}
                <tr className="bg-gray-100 font-bold border-t-2 border-gray-300">
                  <td className="py-3 px-3">Total</td>
                  <td className="py-3 px-3 text-right text-red-600">($${totalContributions.toFixed(1)}M)</td>
                  <td className="py-3 px-3 text-right text-blue-600">${lpReturnOfCapital.toFixed(1)}M</td>
                  <td className="py-3 px-3 text-right text-green-600">${lpPreferredReturn.toFixed(1)}M</td>
                  <td className="py-3 px-3 text-right text-purple-600">${lpCarriedInterest.toFixed(1)}M</td>
                  <td className="py-3 px-3 text-right text-green-700">${(totalLPDistributionsWithCarry - totalContributions).toFixed(1)}M</td>
                  <td className="py-3 px-3 text-right">-</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Key Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* LP Metrics */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg shadow-lg p-6 border-l-4 border-blue-500">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Users className="w-6 h-6 mr-2 text-blue-600" />
              LP Performance Metrics
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Total Contributions</span>
                <span className="text-xl font-bold text-red-600">${totalContributions.toFixed(1)}M</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Total Distributions</span>
                <span className="text-xl font-bold text-green-600">${totalLP.toFixed(1)}M</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t-2 border-blue-200">
                <span className="text-gray-700 font-semibold">Net to LPs</span>
                <span className="text-2xl font-bold text-blue-600">${(totalLP - totalContributions).toFixed(1)}M</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700 font-semibold">LP Multiple (DPI)</span>
                <span className="text-2xl font-bold text-blue-600">{(totalLP / totalContributions).toFixed(2)}x</span>
              </div>
            </div>
          </div>

          {/* GP Metrics */}
          <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg shadow-lg p-6 border-l-4 border-orange-500">
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Building className="w-6 h-6 mr-2 text-orange-600" />
              GP Performance Metrics
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Management Fees (Est.)</span>
                <span className="text-xl font-bold text-gray-600">$20.0M</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Carried Interest</span>
                <span className="text-xl font-bold text-orange-600">${totalGP.toFixed(1)}M</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t-2 border-orange-200">
                <span className="text-gray-700 font-semibold">Total GP Economics</span>
                <span className="text-2xl font-bold text-orange-600">${(totalGP + 20).toFixed(1)}M</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700 font-semibold">Carry % of Profits</span>
                <span className="text-2xl font-bold text-orange-600">{((totalGP / (totalFundDistributions - totalContributions)) * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComprehensiveVCWaterfall;