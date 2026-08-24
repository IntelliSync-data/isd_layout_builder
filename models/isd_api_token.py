import secrets
from datetime import date, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class IsdApiToken(models.Model):
    _name = 'isd.api.token'
    _description = 'API Token'

    token = fields.Char(string='Token', readonly=True, copy=False)
    expires_date = fields.Date(string='Expiration Date')
    created_date = fields.Date(string='Created Date', readonly=True)

    @api.constrains('expires_date')
    def _check_expires_date(self):
        for record in self:
            if not record.expires_date:
                continue
            today = date.today()
            max_date = today + timedelta(days=30)
            if record.expires_date < today:
                raise ValidationError(_('Expiration date cannot be in the past.'))
            if record.expires_date > max_date:
                raise ValidationError(_('Expiration date must be within 30 days from today (%s).') % max_date.strftime('%d/%m/%Y'))

    def action_generate_token(self):
        self.ensure_one()
        if not self.expires_date:
            raise ValidationError(_('Please select an expiration date before generating a token.'))
        self.write({
            'token': secrets.token_hex(32),
            'created_date': fields.Date.today(),
        })

    @api.model
    def get_or_create_singleton(self):
        """Get the singleton record, or create one if none exists."""
        record = self.search([], limit=1)
        if not record:
            record = self.create({})
        return record
