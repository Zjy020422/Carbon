"""
emission_calculator.py - 航空碳排放计算引擎
结合尾迹云检测结果和航班数据，计算CO2当量排放
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import math


@dataclass
class FlightParams:
    """航班参数"""
    icao24: str
    callsign: str
    latitude: float
    longitude: float
    altitude: float  # 气压高度 (米)
    velocity: float  # 地速 (m/s)
    vertical_rate: float  # 爬升/下降率 (m/s)
    timestamp: int
    true_track: float  # 航向角 (度)


@dataclass
class EmissionResult:
    """排放计算结果"""
    co2_direct: float  # 直接CO2排放 (kg)
    co2_contrail: float  # 尾迹云CO2当量 (kg)
    co2_total: float  # 总CO2当量 (kg)
    fuel_burn: float  # 燃油消耗 (kg)
    contrail_coverage: float  # 尾迹云覆盖面积 (km²)
    contrail_intensity: float  # 尾迹云强度 (0-1)
    flight_distance: float  # 飞行距离 (km)
    emission_factor: float  # 排放因子 (kg CO2/km)


class EmissionCalculator:
    """
    航空碳排放计算器

    计算方法：
    1. 直接CO2排放 = 燃油消耗 × 排放因子
    2. 尾迹云CO2当量 = 辐射强迫 × 持续时间 × 面积 × 转换系数
    3. 总排放 = 直接排放 + 尾迹云当量
    """

    # 常量定义
    EF_CO2 = 3.16  # kg CO2 / kg fuel（标准排放因子）
    EF_NOx = 0.013  # kg NOx / kg fuel
    EF_H2O = 1.23  # kg H2O / kg fuel

    # 飞机类型燃油消耗率 (kg/km)
    FUEL_BURN_RATES = {
        'A320': 2.5,
        'A321': 2.7,
        'A330': 5.5,
        'A350': 5.8,
        'B737': 2.4,
        'B747': 12.0,
        'B777': 7.5,
        'B787': 5.5,
        'default': 3.0  # 默认值
    }

    # 尾迹云辐射强迫系数 (W/m²)
    CONTRAIL_RF_BASE = 0.03  # 基准值

    def __init__(self):
        pass

    def estimate_aircraft_type(self, callsign: str) -> str:
        """
        根据呼号估计飞机类型
        实际应用中应使用完整的飞机数据库
        """
        if not callsign:
            return 'default'

        callsign = callsign.upper().strip()

        # 简化的映射逻辑
        type_indicators = {
            'A32': 'A320',
            'A33': 'A330',
            'A35': 'A350',
            'B73': 'B737',
            'B74': 'B747',
            'B77': 'B777',
            'B78': 'B787'
        }

        for indicator, aircraft_type in type_indicators.items():
            if indicator in callsign:
                return aircraft_type

        return 'default'

    def calculate_fuel_burn(
        self,
        distance: float,
        aircraft_type: str = 'default',
        altitude: float = 10000,
        velocity: float = 230
    ) -> float:
        """
        计算燃油消耗

        参数:
            distance: 飞行距离 (km)
            aircraft_type: 飞机型号
            altitude: 高度 (m)
            velocity: 速度 (m/s)

        返回:
            燃油消耗 (kg)
        """
        # 基础燃油消耗率
        base_rate = self.FUEL_BURN_RATES.get(aircraft_type, self.FUEL_BURN_RATES['default'])

        # 高度修正系数（高空燃油效率更高）
        altitude_factor = 1.0
        if altitude > 9000:  # 巡航高度
            altitude_factor = 0.85
        elif altitude > 6000:
            altitude_factor = 0.92
        else:
            altitude_factor = 1.1  # 低空燃油消耗更高

        # 速度修正系数
        optimal_speed = 250  # m/s (约900 km/h)
        speed_factor = 1.0 + 0.001 * abs(velocity - optimal_speed)

        # 总燃油消耗
        fuel_burn = distance * base_rate * altitude_factor * speed_factor

        return fuel_burn

    def calculate_direct_co2(self, fuel_burn: float) -> float:
        """
        计算直接CO2排放

        参数:
            fuel_burn: 燃油消耗 (kg)

        返回:
            CO2排放 (kg)
        """
        return fuel_burn * self.EF_CO2

    def calculate_contrail_co2_equivalent(
        self,
        contrail_mask: np.ndarray,
        pixel_size_km: float = 2.0,  # GOES-16 ABI像素大小约2km
        duration_hours: float = 3.0,  # 尾迹云平均持续时间
        intensity: Optional[float] = None
    ) -> Tuple[float, float, float]:
        """
        计算尾迹云的CO2当量排放

        基于辐射强迫(RF)方法：
        CO2_eq = RF × Duration × Area × Conversion_Factor

        参数:
            contrail_mask: 尾迹云掩码 (256×256)
            pixel_size_km: 每个像素的实际尺寸 (km)
            duration_hours: 尾迹云持续时间 (小时)
            intensity: 尾迹云强度 (0-1)，如果为None则从mask计算

        返回:
            (CO2当量 kg, 覆盖面积 km², 强度)
        """
        # 计算覆盖面积
        contrail_pixels = np.sum(contrail_mask > 0.5)
        coverage_area = contrail_pixels * (pixel_size_km ** 2)  # km²

        # 计算强度
        if intensity is None:
            intensity = np.mean(contrail_mask[contrail_mask > 0.5]) if contrail_pixels > 0 else 0.0

        # 辐射强迫计算
        rf_total = self.CONTRAIL_RF_BASE * intensity * coverage_area  # W/m² × km²

        # 转换为能量 (kWh)
        # RF (W/m²) × Area (m²) × Time (h) → kWh
        energy_impact = rf_total * coverage_area * 1e6 * duration_hours / 1000  # kWh

        # CO2当量转换
        # 使用IPCC转换系数：1 kWh ≈ 0.5 kg CO2eq (取决于能源组合)
        # 尾迹云的全球变暖潜能值(GWP)约为2000-3000倍于CO2
        # 这里使用简化模型
        co2_equivalent = energy_impact * 0.5 * 2.5  # kg CO2eq

        return co2_equivalent, coverage_area, intensity

    def calculate_flight_emissions(
        self,
        flight_track: pd.DataFrame,
        contrail_mask: Optional[np.ndarray] = None,
        aircraft_type: Optional[str] = None
    ) -> EmissionResult:
        """
        计算单个航班的总排放

        参数:
            flight_track: 航迹DataFrame，包含lat, lon, altitude, time等
            contrail_mask: 尾迹云掩码 (可选)
            aircraft_type: 飞机型号 (可选，会自动推断)

        返回:
            EmissionResult对象
        """
        # 推断飞机类型
        if aircraft_type is None:
            callsign = flight_track['callsign'].iloc[0] if 'callsign' in flight_track else ''
            aircraft_type = self.estimate_aircraft_type(callsign)

        # 计算飞行距离
        flight_distance = self._calculate_track_distance(flight_track)

        # 计算平均高度和速度
        avg_altitude = flight_track['baro_altitude'].mean()
        avg_velocity = flight_track.get('velocity', pd.Series([230])).mean()

        # 燃油消耗
        fuel_burn = self.calculate_fuel_burn(
            distance=flight_distance,
            aircraft_type=aircraft_type,
            altitude=avg_altitude,
            velocity=avg_velocity
        )

        # 直接CO2排放
        co2_direct = self.calculate_direct_co2(fuel_burn)

        # 尾迹云CO2当量
        co2_contrail = 0.0
        contrail_coverage = 0.0
        contrail_intensity = 0.0

        if contrail_mask is not None:
            co2_contrail, contrail_coverage, contrail_intensity = \
                self.calculate_contrail_co2_equivalent(contrail_mask)

        # 总排放
        co2_total = co2_direct + co2_contrail

        # 排放因子
        emission_factor = co2_total / flight_distance if flight_distance > 0 else 0.0

        return EmissionResult(
            co2_direct=co2_direct,
            co2_contrail=co2_contrail,
            co2_total=co2_total,
            fuel_burn=fuel_burn,
            contrail_coverage=contrail_coverage,
            contrail_intensity=contrail_intensity,
            flight_distance=flight_distance,
            emission_factor=emission_factor
        )

    def _calculate_track_distance(self, track: pd.DataFrame) -> float:
        """
        计算航迹总距离

        使用Haversine公式计算球面距离

        参数:
            track: 航迹DataFrame，必须包含latitude和longitude列

        返回:
            总距离 (km)
        """
        if len(track) < 2:
            return 0.0

        lats = track['latitude'].values
        lons = track['longitude'].values

        total_distance = 0.0

        for i in range(len(track) - 1):
            d = self._haversine_distance(
                lats[i], lons[i],
                lats[i+1], lons[i+1]
            )
            total_distance += d

        return total_distance

    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """
        Haversine公式计算两点间球面距离

        参数:
            lat1, lon1: 点1的纬度和经度 (度)
            lat2, lon2: 点2的纬度和经度 (度)

        返回:
            距离 (km)
        """
        R = 6371.0  # 地球半径 (km)

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c

        return distance


class BatchEmissionCalculator:
    """批量航班碳排放计算器"""

    def __init__(self, carbon_market='EU_ETS'):
        """
        初始化批量计算器

        参数:
            carbon_market: 碳市场（EU_ETS, CORSIA, CHINA等）
        """
        self.emission_calc = EmissionCalculator()

        # 尝试导入碳交易模块
        try:
            from .carbon_trading import CarbonTradingCalculator
            self.carbon_calc = CarbonTradingCalculator(market=carbon_market)
            self.has_carbon_trading = True
        except ImportError:
            self.carbon_calc = None
            self.has_carbon_trading = False

    def process_flight_csv(
        self,
        input_csv,
        output_csv,
        contrail_masks_dir=None
    ):
        """
        批量处理航班CSV数据并计算碳排放

        参数:
            input_csv: 输入航班CSV（需包含速度、高度等字段）
            output_csv: 输出结果CSV
            contrail_masks_dir: 尾迹云掩码目录（可选）

        返回:
            结果DataFrame
        """
        print("="*70)
        print("批量航班碳排放计算")
        print("="*70)

        # 读取数据
        print(f"\n[1/3] 读取航班数据: {input_csv}")
        df = pd.read_csv(input_csv)
        print(f"  航班数: {len(df)}")

        # 计算排放
        print(f"\n[2/3] 计算碳排放...")
        results = []

        for idx, flight in df.iterrows():
            try:
                # 构建航迹数据
                flight_track = pd.DataFrame({
                    'latitude': [flight['latitude_1'], flight['latitude_2']],
                    'longitude': [flight['longitude_1'], flight['longitude_2']],
                    'baro_altitude': [flight.get('altitude_1', 0), flight.get('altitude_2', 0)],
                    'velocity': [flight.get('avg_ground_speed_ms', 230)] * 2,
                    'callsign': [flight.get('callsign', 'UNKNOWN')] * 2
                })

                # 获取飞机型号
                aircraft_type = flight.get('typecode', 'default')
                if pd.isna(aircraft_type):
                    aircraft_type = 'default'

                # 计算排放
                emission_result = self.emission_calc.calculate_flight_emissions(
                    flight_track=flight_track,
                    aircraft_type=aircraft_type
                )

                # 基础结果
                result = {
                    'record_id': flight.get('record_id', ''),
                    'callsign': flight.get('callsign', ''),
                    'icao24': flight.get('icao24', ''),
                    'typecode': aircraft_type,
                    'flight_distance_km': emission_result.flight_distance,
                    'fuel_burn_kg': emission_result.fuel_burn,
                    'co2_direct_kg': emission_result.co2_direct,
                    'co2_contrail_kg': emission_result.co2_contrail,
                    'co2_total_kg': emission_result.co2_total,
                    'emission_factor_kg_per_km': emission_result.emission_factor
                }

                # 添加碳交易成本（如果可用）
                if self.has_carbon_trading:
                    carbon_cost = self.carbon_calc.calculate_flight_carbon_cost(
                        co2_emissions_kg=emission_result.co2_total,
                        flight_distance_km=emission_result.flight_distance
                    )
                    result['carbon_cost_usd'] = carbon_cost.carbon_cost_total
                    result['carbon_cost_per_km_usd'] = carbon_cost.carbon_cost_per_km

                results.append(result)

                if (idx + 1) % 10 == 0:
                    print(f"  进度: {idx+1}/{len(df)} ({(idx+1)/len(df)*100:.1f}%)")

            except Exception as e:
                print(f"  [WARNING] 处理航班 {flight.get('callsign', idx)} 时出错: {e}")
                continue

        # 创建结果DataFrame
        print(f"\n[3/3] 保存结果...")
        df_results = pd.DataFrame(results)

        if len(df_results) > 0:
            df_results.to_csv(output_csv, index=False)

            # 统计
            total_co2 = df_results['co2_total_kg'].sum()
            total_fuel = df_results['fuel_burn_kg'].sum()

            print(f"\n统计:")
            print(f"  成功处理: {len(df_results)}/{len(df)} 航班")
            print(f"  总CO2排放: {total_co2/1000:.1f} tonnes")
            print(f"  总燃油消耗: {total_fuel/1000:.1f} tonnes")
            if self.has_carbon_trading:
                total_cost = df_results['carbon_cost_usd'].sum()
                print(f"  总碳成本: ${total_cost:,.2f}")

            print(f"\n输出文件: {output_csv}")

        return df_results


class EmissionReportGenerator:
    """排放报告生成器"""

    def __init__(self):
        self.calculator = EmissionCalculator()

    def generate_flight_report(
        self,
        emission_result: EmissionResult,
        flight_info: Dict
    ) -> str:
        """
        生成单个航班的排放报告

        参数:
            emission_result: 排放计算结果
            flight_info: 航班信息字典

        返回:
            格式化的报告字符串
        """
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║              AVIATION EMISSION REPORT                         ║
╠══════════════════════════════════════════════════════════════╣
║ Flight Information                                            ║
║   Callsign:       {flight_info.get('callsign', 'N/A'):<45} ║
║   ICAO24:         {flight_info.get('icao24', 'N/A'):<45} ║
║   Aircraft Type:  {flight_info.get('aircraft_type', 'N/A'):<45} ║
║   Distance:       {emission_result.flight_distance:>10.1f} km                 ║
╠══════════════════════════════════════════════════════════════╣
║ Fuel Consumption                                              ║
║   Total Fuel:     {emission_result.fuel_burn:>10.1f} kg                 ║
╠══════════════════════════════════════════════════════════════╣
║ CO₂ Emissions                                                 ║
║   Direct CO₂:     {emission_result.co2_direct:>10.1f} kg                 ║
║   Contrail CO₂eq: {emission_result.co2_contrail:>10.1f} kg                 ║
║   ─────────────────────────────────────────────────────────  ║
║   TOTAL CO₂eq:    {emission_result.co2_total:>10.1f} kg                 ║
║                                                               ║
║   Emission Factor: {emission_result.emission_factor:>9.2f} kg CO₂/km          ║
╠══════════════════════════════════════════════════════════════╣
║ Contrail Impact                                               ║
║   Coverage Area:  {emission_result.contrail_coverage:>10.1f} km²                ║
║   Intensity:      {emission_result.contrail_intensity:>10.2%}                     ║
╠══════════════════════════════════════════════════════════════╣
║ Environmental Equivalent                                      ║
║   🌳 Trees needed to offset (annual): {int(emission_result.co2_total / 21):>6} ║
║   🚗 Car miles equivalent:           {int(emission_result.co2_total / 0.404):>6} miles    ║
╚══════════════════════════════════════════════════════════════╝
        """

        return report.strip()

    def generate_fleet_summary(
        self,
        emission_results: list,
        airline_name: str = "Unknown Airline"
    ) -> str:
        """
        生成航空公司机队排放汇总

        参数:
            emission_results: 排放结果列表
            airline_name: 航空公司名称

        返回:
            汇总报告
        """
        total_co2 = sum(r.co2_total for r in emission_results)
        total_direct = sum(r.co2_direct for r in emission_results)
        total_contrail = sum(r.co2_contrail for r in emission_results)
        total_fuel = sum(r.fuel_burn for r in emission_results)
        total_distance = sum(r.flight_distance for r in emission_results)
        num_flights = len(emission_results)

        avg_ef = total_co2 / total_distance if total_distance > 0 else 0

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║          FLEET EMISSION SUMMARY REPORT                        ║
╠══════════════════════════════════════════════════════════════╣
║ Airline: {airline_name:<50} ║
║ Period:  [Analysis Period]                                    ║
║ Flights: {num_flights:>5}                                                 ║
╠══════════════════════════════════════════════════════════════╣
║ Total Emissions                                               ║
║   Direct CO₂:      {total_direct:>12,.0f} kg ({total_direct/total_co2*100:>5.1f}%)        ║
║   Contrail CO₂eq:  {total_contrail:>12,.0f} kg ({total_contrail/total_co2*100:>5.1f}%)        ║
║   ────────────────────────────────────────────────────────   ║
║   TOTAL CO₂eq:     {total_co2:>12,.0f} kg (100.0%)        ║
║                                                               ║
║   Total Fuel:      {total_fuel:>12,.0f} kg                   ║
║   Total Distance:  {total_distance:>12,.0f} km                   ║
║   Avg Efficiency:  {avg_ef:>12.2f} kg CO₂/km             ║
╠══════════════════════════════════════════════════════════════╣
║ Per Flight Average                                            ║
║   CO₂eq:           {total_co2/num_flights:>12,.0f} kg/flight            ║
║   Fuel:            {total_fuel/num_flights:>12,.0f} kg/flight            ║
║   Distance:        {total_distance/num_flights:>12,.0f} km/flight            ║
╠══════════════════════════════════════════════════════════════╣
║ Environmental Impact                                          ║
║   🌳 Annual tree offset needed:  {int(total_co2 / 21):>10,}       ║
║   🚗 Car miles equivalent:       {int(total_co2 / 0.404):>10,} miles  ║
║   🏭 CO₂ in tonnes:               {total_co2/1000:>10,.1f} t       ║
╚══════════════════════════════════════════════════════════════╝
        """

        return report.strip()


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例：计算单个航班排放
    calculator = EmissionCalculator()

    # 模拟航迹数据
    flight_track = pd.DataFrame({
        'latitude': [34.0, 35.0, 36.0, 37.0],
        'longitude': [-118.0, -117.5, -117.0, -116.5],
        'baro_altitude': [10000, 10500, 11000, 11000],
        'velocity': [230, 235, 240, 240],
        'callsign': ['UAL123', 'UAL123', 'UAL123', 'UAL123']
    })

    # 模拟尾迹云掩码
    contrail_mask = np.zeros((256, 256))
    contrail_mask[100:150, 120:180] = 0.8  # 模拟尾迹云区域

    # 计算排放
    result = calculator.calculate_flight_emissions(
        flight_track=flight_track,
        contrail_mask=contrail_mask,
        aircraft_type='B737'
    )

    # 生成报告
    report_gen = EmissionReportGenerator()
    flight_info = {
        'callsign': 'UAL123',
        'icao24': 'A12345',
        'aircraft_type': 'B737-800'
    }

    print(report_gen.generate_flight_report(result, flight_info))

    print("\n" + "="*70 + "\n")

    # 示例：机队汇总
    results = [result] * 50  # 模拟50个航班
    print(report_gen.generate_fleet_summary(results, "United Airlines"))
