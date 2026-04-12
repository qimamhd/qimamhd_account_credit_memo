from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_global_report_attachment = fields.Boolean(
        string="Generate Invoice PDF Attachment",
        config_parameter='report_attachment_toggle.use_global'
    )