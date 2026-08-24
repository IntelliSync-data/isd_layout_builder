import secrets
from datetime import date, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class IsdApiToken(models.Model):
    _name = 'isd.api.token'
    _description = 'API Token'

    token = fields.Char(string='Token', readonly=True, copy=False)
    expires_date = fields.Date(string='Ngày hết hạn')
    created_date = fields.Date(string='Ngày tạo', readonly=True)

    @api.constrains('expires_date')
    def _check_expires_date(self):
        for record in self:
            if not record.expires_date:
                continue
            today = date.today()
            max_date = today + timedelta(days=30)
            if record.expires_date < today:
                raise ValidationError(_('Ngày hết hạn không được là ngày trong quá khứ'))
            if record.expires_date > max_date:
                raise ValidationError(_('Ngày hết hạn tối đa là 30 ngày kể từ hôm nay (%s)') % max_date.strftime('%d/%m/%Y'))

    def action_generate_token(self):
        self.ensure_one()
        if not self.expires_date:
            raise ValidationError(_('Vui lòng chọn ngày hết hạn trước khi tạo token'))
        self.write({
            'token': secrets.token_hex(32),
            'created_date': fields.Date.today(),
        })

    @api.model
    def get_or_create_singleton(self):
        """Lấy record duy nhất hoặc tạo mới nếu chưa có"""
        record = self.search([], limit=1)
        if not record:
            record = self.create({})
        return record
