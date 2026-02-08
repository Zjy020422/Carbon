"""
carbon_trading.py - 碳排放交易成本计算模块

基于真实碳市场价格计算航空碳排放的交易成本
支持多个碳市场：EU ETS, CORSIA, 中国碳市场等
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import datetime
import numpy as np


# ==================== 碳市场价格配置 ====================

class CarbonMarketPrices:
    """全球主要碳市场价格 (2024年参考价格)"""

    MARKETS = {
        'EU_ETS': {
            'name': 'EU Emissions Trading System',
            'price_usd': 95.0,  # EUR/tCO₂ (约$95 USD)
            'currency': 'EUR',
            'coverage': '欧盟航空',
            'volatility': 0.25
        },
        'CORSIA': {
            'name': 'ICAO Carbon Offsetting Scheme',
            'price_usd': 20.0,  # USD/tCO₂
            'currency': 'USD',
            'coverage': '国际航线',
            'volatility': 0.15
        },
        'CHINA': {
            'name': '中国全国碳市场',
            'price_usd': 11.0,  # CNY 75/tCO₂ ≈ $11 USD
            'currency': 'CNY',
            'coverage': '中国国内航线',
            'volatility': 0.20
        },
        'UK_ETS': {
            'name': 'UK Emissions Trading Scheme',
            'price_usd': 55.0,  # GBP 45/tCO₂ ≈ $55 USD
            'currency': 'GBP',
            'coverage': '英国航空',
            'volatility': 0.22
        },
        'CALIFORNIA': {
            'name': 'California Cap-and-Trade',
            'price_usd': 32.0,  # USD/tCO₂
            'currency': 'USD',
            'coverage': '加州航空',
            'volatility': 0.18
        }
    }

    @classmethod
    def get_price(cls, market: str = 'EU_ETS') -> float:
        """获取指定碳市场的价格 (USD/tCO₂)"""
        return cls.MARKETS.get(market, cls.MARKETS['EU_ETS'])['price_usd']

    @classmethod
    def list_markets(cls) -> List[str]:
        """列出所有支持的碳市场"""
        return list(cls.MARKETS.keys())


# ==================== 数据类定义 ====================

@dataclass
class CarbonTradingResult:
    """碳交易计算结果"""
    # 基础数据
    co2_emissions_kg: float  # CO₂排放量 (kg)
    co2_emissions_tonnes: float  # CO₂排放量 (tonnes)

    # 成本计算
    carbon_price_per_tonne: float  # 碳价格 (USD/tCO₂)
    carbon_cost_total: float  # 总碳成本 (USD)
    carbon_cost_per_km: float  # 单位距离碳成本 (USD/km)

    # 市场信息
    market_name: str  # 碳市场名称
    calculation_date: str  # 计算日期

    # 可选：旅客成本
    carbon_cost_per_passenger: Optional[float] = None
    num_passengers: Optional[int] = None


@dataclass
class AnnualComplianceResult:
    """年度碳合规计算结果"""
    # 排放数据
    total_emissions_tonnes: float  # 总排放量 (tCO₂)
    free_allowance_tonnes: float  # 免费配额 (tCO₂)
    owned_credits_tonnes: float  # 已有碳信用 (tCO₂)

    # 缺口与成本
    emission_deficit_tonnes: float  # 排放缺口 (tCO₂)
    compliance_cost_usd: float  # 合规成本 (USD)

    # 采购需求
    needs_purchase: bool  # 是否需要购买
    allowances_to_buy_tonnes: float  # 需购买的配额 (tCO₂)

    # 市场信息
    carbon_price_per_tonne: float  # 碳价格 (USD/tCO₂)
    market_name: str  # 碳市场


# ==================== 碳交易计算器 ====================

class CarbonTradingCalculator:
    """
    碳交易成本计算器

    功能:
    1. 计算单个航班的碳交易成本
    2. 计算年度碳合规成本
    3. 优化碳配额购买策略
    4. 预测未来碳成本
    """

    def __init__(
        self,
        market: str = 'EU_ETS',
        custom_price: Optional[float] = None
    ):
        """
        初始化碳交易计算器

        参数:
            market: 碳市场名称 (EU_ETS, CORSIA, CHINA等)
            custom_price: 自定义碳价格 (USD/tCO₂)，覆盖市场价格
        """
        self.market = market
        self.market_info = CarbonMarketPrices.MARKETS.get(market, CarbonMarketPrices.MARKETS['EU_ETS'])

        # 使用自定义价格或市场价格
        if custom_price:
            self.carbon_price = custom_price
        else:
            self.carbon_price = self.market_info['price_usd']

    def calculate_flight_carbon_cost(
        self,
        co2_emissions_kg: float,
        flight_distance_km: float,
        num_passengers: Optional[int] = None
    ) -> CarbonTradingResult:
        """
        计算单个航班的碳交易成本

        参数:
            co2_emissions_kg: CO₂排放量 (kg)，来自EmissionCalculator
            flight_distance_km: 飞行距离 (km)
            num_passengers: 旅客数量 (可选)

        返回:
            CarbonTradingResult 对象
        """
        # 转换为tonnes
        co2_tonnes = co2_emissions_kg / 1000.0

        # 计算总碳成本
        carbon_cost_total = co2_tonnes * self.carbon_price

        # 单位距离成本
        carbon_cost_per_km = carbon_cost_total / flight_distance_km if flight_distance_km > 0 else 0

        # 旅客成本
        carbon_cost_per_pax = None
        if num_passengers and num_passengers > 0:
            carbon_cost_per_pax = carbon_cost_total / num_passengers

        return CarbonTradingResult(
            co2_emissions_kg=co2_emissions_kg,
            co2_emissions_tonnes=co2_tonnes,
            carbon_price_per_tonne=self.carbon_price,
            carbon_cost_total=carbon_cost_total,
            carbon_cost_per_km=carbon_cost_per_km,
            market_name=self.market_info['name'],
            calculation_date=datetime.now().strftime('%Y-%m-%d'),
            carbon_cost_per_passenger=carbon_cost_per_pax,
            num_passengers=num_passengers
        )

    def calculate_annual_compliance_cost(
        self,
        total_emissions_tonnes: float,
        free_allowance_tonnes: float = 0.0,
        owned_credits_tonnes: float = 0.0
    ) -> AnnualComplianceResult:
        """
        计算年度碳合规成本

        参数:
            total_emissions_tonnes: 年度总排放量 (tCO₂)
            free_allowance_tonnes: 政府分配的免费配额 (tCO₂)
            owned_credits_tonnes: 企业已持有的碳信用 (tCO₂)

        返回:
            AnnualComplianceResult 对象
        """
        # 计算排放缺口
        emission_deficit = max(0, total_emissions_tonnes - free_allowance_tonnes - owned_credits_tonnes)

        # 合规成本
        compliance_cost = emission_deficit * self.carbon_price

        # 是否需要购买
        needs_purchase = emission_deficit > 0

        return AnnualComplianceResult(
            total_emissions_tonnes=total_emissions_tonnes,
            free_allowance_tonnes=free_allowance_tonnes,
            owned_credits_tonnes=owned_credits_tonnes,
            emission_deficit_tonnes=emission_deficit,
            compliance_cost_usd=compliance_cost,
            needs_purchase=needs_purchase,
            allowances_to_buy_tonnes=emission_deficit,
            carbon_price_per_tonne=self.carbon_price,
            market_name=self.market_info['name']
        )

    def optimize_purchase_strategy(
        self,
        deficit_tonnes: float,
        eua_price: float,  # EU Allowance价格
        credit_price: float,  # 碳信用价格
        credit_limit_ratio: float = 0.15  # 碳信用使用限制 (默认15%)
    ) -> Dict:
        """
        优化碳配额购买策略

        参数:
            deficit_tonnes: 排放缺口 (tCO₂)
            eua_price: 欧盟配额价格 (USD/tCO₂)
            credit_price: 碳信用价格 (USD/tCO₂)
            credit_limit_ratio: 碳信用最大使用比例

        返回:
            优化策略字典
        """
        # 计算碳信用最大使用量
        max_credits = deficit_tonnes * credit_limit_ratio

        # 如果碳信用更便宜，优先使用
        if credit_price < eua_price:
            credits_to_buy = min(deficit_tonnes, max_credits)
            eua_to_buy = deficit_tonnes - credits_to_buy
        else:
            credits_to_buy = 0
            eua_to_buy = deficit_tonnes

        # 计算成本
        total_cost = (eua_to_buy * eua_price) + (credits_to_buy * credit_price)
        all_eua_cost = deficit_tonnes * eua_price
        savings = all_eua_cost - total_cost

        return {
            'eua_to_purchase_tonnes': eua_to_buy,
            'credits_to_purchase_tonnes': credits_to_buy,
            'total_cost_usd': total_cost,
            'savings_usd': savings,
            'average_price_per_tonne': total_cost / deficit_tonnes if deficit_tonnes > 0 else 0,
            'recommendation': 'Use carbon credits' if savings > 0 else 'Use EU Allowances only'
        }

    def forecast_carbon_cost(
        self,
        current_emissions_tonnes: float,
        years: int = 5,
        annual_growth_rate: float = 0.08  # 8% 年增长率
    ) -> List[Dict]:
        """
        预测未来碳成本趋势

        参数:
            current_emissions_tonnes: 当前年度排放 (tCO₂)
            years: 预测年数
            annual_growth_rate: 碳价格年增长率 (默认8%)

        返回:
            未来年份的成本预测列表
        """
        forecast = []
        base_year = datetime.now().year

        for year in range(1, years + 1):
            future_price = self.carbon_price * ((1 + annual_growth_rate) ** year)
            future_cost = current_emissions_tonnes * future_price

            forecast.append({
                'year': base_year + year,
                'carbon_price_usd_per_tonne': round(future_price, 2),
                'total_cost_usd': round(future_cost, 2),
                'cost_increase_percent': round((future_cost / (current_emissions_tonnes * self.carbon_price) - 1) * 100, 1)
            })

        return forecast


# ==================== 报告生成器 ====================

class CarbonTradingReportGenerator:
    """碳交易成本报告生成器"""

    @staticmethod
    def generate_flight_carbon_report(result: CarbonTradingResult) -> str:
        """生成单个航班的碳成本报告"""
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║            FLIGHT CARBON TRADING COST REPORT                  ║
╠══════════════════════════════════════════════════════════════╣
║ Market: {result.market_name:<50} ║
║ Date:   {result.calculation_date:<50} ║
╠══════════════════════════════════════════════════════════════╣
║ Emissions                                                     ║
║   CO2 Emissions:    {result.co2_emissions_kg:>10,.0f} kg                  ║
║                     {result.co2_emissions_tonnes:>10,.2f} tonnes              ║
╠══════════════════════════════════════════════════════════════╣
║ Carbon Costs                                                  ║
║   Carbon Price:     ${result.carbon_price_per_tonne:>10,.2f} /tCO2             ║
║   Total Cost:       ${result.carbon_cost_total:>10,.2f}                    ║
║   Cost per km:      ${result.carbon_cost_per_km:>10,.4f} /km                ║
"""

        if result.carbon_cost_per_passenger is not None:
            report += f"""║   Cost per Passenger: ${result.carbon_cost_per_passenger:>8,.2f} /pax              ║
║   Passengers:       {result.num_passengers:>10,}                      ║
"""

        report += """╚══════════════════════════════════════════════════════════════╝
        """

        return report.strip()

    @staticmethod
    def generate_annual_compliance_report(result: AnnualComplianceResult) -> str:
        """生成年度碳合规报告"""

        surplus_deficit = "DEFICIT" if result.needs_purchase else "SURPLUS"
        status_color = "[!]" if result.needs_purchase else "[OK]"

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║         ANNUAL CARBON COMPLIANCE COST REPORT                  ║
╠══════════════════════════════════════════════════════════════╣
║ Market: {result.market_name:<50} ║
║ Status: {status_color} {surplus_deficit:<46} ║
╠══════════════════════════════════════════════════════════════╣
║ Emissions Balance                                             ║
║   Total Emissions:        {result.total_emissions_tonnes:>12,.0f} tCO2           ║
║   Free Allowance:         {result.free_allowance_tonnes:>12,.0f} tCO2           ║
║   Owned Credits:          {result.owned_credits_tonnes:>12,.0f} tCO2           ║
║   ----------------------------------------------------------║
║   Emission Deficit:       {result.emission_deficit_tonnes:>12,.0f} tCO2           ║
╠══════════════════════════════════════════════════════════════╣
║ Compliance Costs                                              ║
║   Carbon Price:           ${result.carbon_price_per_tonne:>11,.2f} /tCO2          ║
║   Allowances to Buy:      {result.allowances_to_buy_tonnes:>12,.0f} tCO2           ║
║   ----------------------------------------------------------║
║   TOTAL COMPLIANCE COST:  ${result.compliance_cost_usd:>11,.2f}               ║
╠══════════════════════════════════════════════════════════════╣
║ Purchase Recommendation                                       ║
║   {"Purchase Required" if result.needs_purchase else "No Purchase Needed":<60} ║
╚══════════════════════════════════════════════════════════════╝
        """

        return report.strip()


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("="*70)
    print("CARBON TRADING CALCULATOR - DEMO")
    print("="*70)

    # 创建计算器
    calc_eu = CarbonTradingCalculator(market='EU_ETS')
    calc_corsia = CarbonTradingCalculator(market='CORSIA')

    # 示例1: 单个航班碳成本
    print("\n[Example 1] Single Flight Carbon Cost")
    print("-"*70)

    flight_result_eu = calc_eu.calculate_flight_carbon_cost(
        co2_emissions_kg=15000,  # 15 tonnes
        flight_distance_km=2500,
        num_passengers=180
    )

    report_gen = CarbonTradingReportGenerator()
    print(report_gen.generate_flight_carbon_report(flight_result_eu))

    # 对比CORSIA市场
    flight_result_corsia = calc_corsia.calculate_flight_carbon_cost(
        co2_emissions_kg=15000,
        flight_distance_km=2500,
        num_passengers=180
    )

    print(f"\n[Comparison] Same flight under CORSIA:")
    print(f"  Total Cost: ${flight_result_corsia.carbon_cost_total:,.2f}")
    print(f"  Savings vs EU ETS: ${flight_result_eu.carbon_cost_total - flight_result_corsia.carbon_cost_total:,.2f}")

    # 示例2: 年度合规成本
    print("\n\n[Example 2] Annual Compliance Cost")
    print("-"*70)

    annual_result = calc_eu.calculate_annual_compliance_cost(
        total_emissions_tonnes=500000,
        free_allowance_tonnes=450000,
        owned_credits_tonnes=20000
    )

    print(report_gen.generate_annual_compliance_report(annual_result))

    # 示例3: 采购策略优化
    print("\n\n[Example 3] Purchase Strategy Optimization")
    print("-"*70)

    strategy = calc_eu.optimize_purchase_strategy(
        deficit_tonnes=30000,
        eua_price=95.0,
        credit_price=30.0,
        credit_limit_ratio=0.15
    )

    print(f"Emission Deficit: {30000:,.0f} tCO2")
    print(f"\nOptimal Strategy:")
    print(f"  EU Allowances to buy: {strategy['eua_to_purchase_tonnes']:,.0f} tCO2")
    print(f"  Carbon Credits to buy: {strategy['credits_to_purchase_tonnes']:,.0f} tCO2")
    print(f"  Total Cost: ${strategy['total_cost_usd']:,.2f}")
    print(f"  Savings: ${strategy['savings_usd']:,.2f}")
    print(f"  Recommendation: {strategy['recommendation']}")

    # 示例4: 成本预测
    print("\n\n[Example 4] Carbon Cost Forecast (5 years)")
    print("-"*70)

    forecast = calc_eu.forecast_carbon_cost(
        current_emissions_tonnes=500000,
        years=5,
        annual_growth_rate=0.08
    )

    print(f"{'Year':<8} {'Price ($/tCO2)':<18} {'Total Cost':<18} {'Increase %':<12}")
    print("-"*70)
    for f in forecast:
        print(f"{f['year']:<8} ${f['carbon_price_usd_per_tonne']:<17,.2f} ${f['total_cost_usd']:<17,.2f} +{f['cost_increase_percent']:<11.1f}%")

    print("\n" + "="*70)
    print("Available Carbon Markets:")
    for market_code in CarbonMarketPrices.list_markets():
        market = CarbonMarketPrices.MARKETS[market_code]
        print(f"  {market_code:<12} - {market['name']:<40} ${market['price_usd']:.2f}/tCO2")
