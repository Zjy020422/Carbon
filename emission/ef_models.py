"""
ef_models.py - 排放因子模型
包含各种飞机类型的详细排放因子数据库
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class AircraftEmissionFactors:
    """飞机排放因子数据类"""
    aircraft_type: str
    fuel_burn_rate_cruise: float  # kg/km (巡航)
    fuel_burn_rate_climb: float  # kg/km (爬升)
    fuel_burn_rate_descent: float  # kg/km (下降)
    ef_co2: float  # kg CO2 / kg fuel
    ef_nox: float  # kg NOx / kg fuel
    ef_h2o: float  # kg H2O / kg fuel
    ef_soot: float  # kg Soot / kg fuel
    contrail_probability: float  # 尾迹云形成概率 (0-1)


class EmissionFactorDatabase:
    """排放因子数据库"""

    # 详细的飞机排放因子数据
    AIRCRAFT_DATA: Dict[str, AircraftEmissionFactors] = {
        # 窄体客机
        'A320': AircraftEmissionFactors(
            aircraft_type='A320',
            fuel_burn_rate_cruise=2.5,
            fuel_burn_rate_climb=3.5,
            fuel_burn_rate_descent=1.2,
            ef_co2=3.16,
            ef_nox=0.013,
            ef_h2o=1.23,
            ef_soot=0.0004,
            contrail_probability=0.35
        ),
        'A321': AircraftEmissionFactors(
            aircraft_type='A321',
            fuel_burn_rate_cruise=2.7,
            fuel_burn_rate_climb=3.8,
            fuel_burn_rate_descent=1.3,
            ef_co2=3.16,
            ef_nox=0.013,
            ef_h2o=1.23,
            ef_soot=0.0004,
            contrail_probability=0.38
        ),
        'B737-800': AircraftEmissionFactors(
            aircraft_type='B737-800',
            fuel_burn_rate_cruise=2.4,
            fuel_burn_rate_climb=3.3,
            fuel_burn_rate_descent=1.1,
            ef_co2=3.16,
            ef_nox=0.014,
            ef_h2o=1.23,
            ef_soot=0.0005,
            contrail_probability=0.33
        ),
        'B737-900': AircraftEmissionFactors(
            aircraft_type='B737-900',
            fuel_burn_rate_cruise=2.6,
            fuel_burn_rate_climb=3.6,
            fuel_burn_rate_descent=1.2,
            ef_co2=3.16,
            ef_nox=0.014,
            ef_h2o=1.23,
            ef_soot=0.0005,
            contrail_probability=0.36
        ),

        # 宽体客机
        'A330-300': AircraftEmissionFactors(
            aircraft_type='A330-300',
            fuel_burn_rate_cruise=5.5,
            fuel_burn_rate_climb=7.5,
            fuel_burn_rate_descent=2.5,
            ef_co2=3.16,
            ef_nox=0.012,
            ef_h2o=1.23,
            ef_soot=0.0003,
            contrail_probability=0.45
        ),
        'A350-900': AircraftEmissionFactors(
            aircraft_type='A350-900',
            fuel_burn_rate_cruise=5.8,
            fuel_burn_rate_climb=8.0,
            fuel_burn_rate_descent=2.6,
            ef_co2=3.16,
            ef_nox=0.011,
            ef_h2o=1.23,
            ef_soot=0.0003,
            contrail_probability=0.42
        ),
        'B777-300ER': AircraftEmissionFactors(
            aircraft_type='B777-300ER',
            fuel_burn_rate_cruise=7.5,
            fuel_burn_rate_climb=10.0,
            fuel_burn_rate_descent=3.2,
            ef_co2=3.16,
            ef_nox=0.013,
            ef_h2o=1.23,
            ef_soot=0.0004,
            contrail_probability=0.48
        ),
        'B787-9': AircraftEmissionFactors(
            aircraft_type='B787-9',
            fuel_burn_rate_cruise=5.5,
            fuel_burn_rate_climb=7.8,
            fuel_burn_rate_descent=2.5,
            ef_co2=3.16,
            ef_nox=0.010,
            ef_h2o=1.23,
            ef_soot=0.0002,
            contrail_probability=0.40
        ),

        # 超大型客机
        'B747-400': AircraftEmissionFactors(
            aircraft_type='B747-400',
            fuel_burn_rate_cruise=12.0,
            fuel_burn_rate_climb=16.0,
            fuel_burn_rate_descent=5.0,
            ef_co2=3.16,
            ef_nox=0.015,
            ef_h2o=1.23,
            ef_soot=0.0006,
            contrail_probability=0.55
        ),
        'A380': AircraftEmissionFactors(
            aircraft_type='A380',
            fuel_burn_rate_cruise=11.5,
            fuel_burn_rate_climb=15.5,
            fuel_burn_rate_descent=4.8,
            ef_co2=3.16,
            ef_nox=0.012,
            ef_h2o=1.23,
            ef_soot=0.0004,
            contrail_probability=0.52
        ),

        # 默认值（中型客机）
        'default': AircraftEmissionFactors(
            aircraft_type='default',
            fuel_burn_rate_cruise=3.0,
            fuel_burn_rate_climb=4.2,
            fuel_burn_rate_descent=1.5,
            ef_co2=3.16,
            ef_nox=0.013,
            ef_h2o=1.23,
            ef_soot=0.0004,
            contrail_probability=0.35
        )
    }

    @classmethod
    def get_emission_factors(
        cls,
        aircraft_type: str
    ) -> AircraftEmissionFactors:
        """
        获取飞机排放因子

        参数:
            aircraft_type: 飞机型号

        返回:
            排放因子数据
        """
        # 标准化飞机型号
        aircraft_type = aircraft_type.upper().strip()

        # 精确匹配
        if aircraft_type in cls.AIRCRAFT_DATA:
            return cls.AIRCRAFT_DATA[aircraft_type]

        # 模糊匹配
        for key in cls.AIRCRAFT_DATA:
            if key in aircraft_type or aircraft_type in key:
                return cls.AIRCRAFT_DATA[key]

        # 返回默认值
        return cls.AIRCRAFT_DATA['default']

    @classmethod
    def list_aircraft_types(cls) -> list:
        """列出所有支持的飞机型号"""
        return [k for k in cls.AIRCRAFT_DATA.keys() if k != 'default']

    @classmethod
    def compare_aircraft(cls, types: list) -> Dict:
        """
        对比多个飞机型号的排放

        参数:
            types: 飞机型号列表

        返回:
            对比数据
        """
        comparison = {}
        for aircraft_type in types:
            ef = cls.get_emission_factors(aircraft_type)
            comparison[aircraft_type] = {
                'cruise_burn': ef.fuel_burn_rate_cruise,
                'co2_factor': ef.ef_co2,
                'contrail_prob': ef.contrail_probability
            }
        return comparison


# ==================== 使用示例 ====================

if __name__ == "__main__":
    db = EmissionFactorDatabase()

    # 获取特定飞机排放因子
    ef_a320 = db.get_emission_factors('A320')
    print(f"\nA320 排放因子:")
    print(f"  巡航燃油消耗: {ef_a320.fuel_burn_rate_cruise} kg/km")
    print(f"  CO2排放因子: {ef_a320.ef_co2} kg CO2/kg fuel")
    print(f"  尾迹云概率: {ef_a320.contrail_probability:.0%}")

    # 对比飞机
    print(f"\n飞机对比:")
    comparison = db.compare_aircraft(['A320', 'B737-800', 'A350-900'])
    for aircraft, data in comparison.items():
        print(f"  {aircraft}: {data['cruise_burn']} kg/km, "
              f"尾迹云概率 {data['contrail_prob']:.0%}")
