from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestHrCalculate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Estructuras salariales creadas por los datos XML
        cls.structure_full_time = cls.env.ref('hr_calculate.structure_full_time')
        cls.structure_part_time = cls.env.ref('hr_calculate.structure_part_time')
        cls.structure_temporary = cls.env.ref('hr_calculate.structure_temporary')

        # Crear empleados
        cls.employee_full = cls.env['hr.employee'].create({
            'name': 'Empleado Tiempo Completo',
        })
        cls.employee_part = cls.env['hr.employee'].create({
            'name': 'Empleado Medio Tiempo',
        })
        cls.employee_temp = cls.env['hr.employee'].create({
            'name': 'Empleado Temporal',
        })
        cls.employee_no_type = cls.env['hr.employee'].create({
            'name': 'Empleado Sin Tipo',
        })

        # Crear contratos
        cls.contract_full = cls.env['hr.contract'].create({
            'name': 'Contrato Tiempo Completo',
            'employee_id': cls.employee_full.id,
            'wage': 1000.0,
            'contract_type': 'full_time',
            'state': 'open',
            'date_start': '2026-01-01',
            'structure_type_id': cls.env.ref('hr_calculate.structure_type_full_time').id,
        })
        cls.contract_part = cls.env['hr.contract'].create({
            'name': 'Contrato Medio Tiempo',
            'employee_id': cls.employee_part.id,
            'wage': 500.0,
            'contract_type': 'part_time',
            'state': 'open',
            'date_start': '2026-01-01',
            'structure_type_id': cls.env.ref('hr_calculate.structure_type_part_time').id,
        })
        cls.contract_temp = cls.env['hr.contract'].create({
            'name': 'Contrato Temporal',
            'employee_id': cls.employee_temp.id,
            'wage': 800.0,
            'contract_type': 'temporary',
            'state': 'open',
            'date_start': '2026-01-01',
            'structure_type_id': cls.env.ref('hr_calculate.structure_type_temporary').id,
        })
        cls.contract_no_type = cls.env['hr.contract'].create({
            'name': 'Contrato Sin Tipo',
            'employee_id': cls.employee_no_type.id,
            'wage': 800.0,
            'state': 'open',
            'date_start': '2026-01-01',
            'structure_type_id': cls.env.ref('hr_calculate.structure_type_full_time').id,
        })

    def _create_payslip(self, employee, contract, structure):
        payslip = self.env['hr.payslip'].create({
            'name': f'Nómina {employee.name}',
            'employee_id': employee.id,
            'contract_id': contract.id,
            'struct_id': structure.id,
            'date_from': '2026-01-01',
            'date_to': '2026-01-31',
        })
        payslip.compute_sheet()
        return payslip

    def test_full_time_has_vacation_benefit(self):
        """Tiempo completo debe tener beneficio de vacaciones"""
        payslip = self._create_payslip(
            self.employee_full,
            self.contract_full,
            self.structure_full_time,
        )
        codes = payslip.line_ids.mapped('code')
        self.assertIn('VACATION', codes,
            'Tiempo completo debe tener línea de Vacaciones')

    def test_full_time_has_severance_benefit(self):
        """Tiempo completo debe tener beneficio de prestaciones"""
        payslip = self._create_payslip(
            self.employee_full,
            self.contract_full,
            self.structure_full_time,
        )
        codes = payslip.line_ids.mapped('code')
        self.assertIn('SEVERANCE', codes,
            'Tiempo completo debe tener línea de Prestaciones')

    def test_full_time_has_bonus_benefit(self):
        """Tiempo completo debe tener bono"""
        payslip = self._create_payslip(
            self.employee_full,
            self.contract_full,
            self.structure_full_time,
        )
        codes = payslip.line_ids.mapped('code')
        self.assertIn('BONUS', codes,
            'Tiempo completo debe tener línea de Bono')

    def test_part_time_has_vacation_benefit(self):
        """Medio tiempo debe tener beneficio de vacaciones"""
        payslip = self._create_payslip(
            self.employee_part,
            self.contract_part,
            self.structure_part_time,
        )
        codes = payslip.line_ids.mapped('code')
        self.assertIn('VACATION', codes,
            'Medio tiempo debe tener línea de Vacaciones')

    def test_part_time_has_no_bonus(self):
        """Medio tiempo NO debe tener bono"""
        payslip = self._create_payslip(
            self.employee_part,
            self.contract_part,
            self.structure_part_time,
        )
        codes = payslip.line_ids.mapped('code')
        self.assertNotIn('BONUS', codes,
            'Medio tiempo no debe tener línea de Bono')

    def test_temporary_has_bonus(self):
        """Temporal debe tener bono"""
        payslip = self._create_payslip(
            self.employee_temp,
            self.contract_temp,
            self.structure_temporary,
        )
        codes = payslip.line_ids.mapped('code')
        self.assertIn('BONUS', codes,
            'Temporal debe tener línea de Bono')

    def test_temporary_has_no_vacation(self):
        """Temporal NO debe tener vacaciones"""
        payslip = self._create_payslip(
            self.employee_temp,
            self.contract_temp,
            self.structure_temporary,
        )
        codes = payslip.line_ids.mapped('code')
        self.assertNotIn('VACATION', codes,
            'Temporal no debe tener línea de Vacaciones')

    def test_no_type_has_no_benefits(self):
        """Caso límite: contrato sin tipo no tiene beneficios adicionales"""
        payslip = self._create_payslip(
            self.employee_no_type,
            self.contract_no_type,
            self.structure_full_time,
        )
        codes = payslip.line_ids.mapped('code')
        self.assertNotIn('VACATION', codes,
            'Sin tipo de contrato no debe tener Vacaciones')
        self.assertNotIn('SEVERANCE', codes,
            'Sin tipo de contrato no debe tener Prestaciones')
        self.assertNotIn('BONUS', codes,
            'Sin tipo de contrato no debe tener Bono')
