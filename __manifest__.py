{
    'name': 'Custom CRM PROPIFY PRO',
    'version': '1.0',
    'depends': ['base', 'crm', 'web', 'mail', 'crm_iap_mine', 'gamification'],
    'data': [
        'security/ir.model.access.csv',
        'security/crm_security.xml',
        'security/ir.ui.menu.xml',
        'views/crm_views.xml',
        'views/crm_lead_form_view.xml',
        'views/crm_lead_kanban_view.xml',
        'views/favicon_inherit.xml',
        'views/header_mod.xml',
        'views/crm_prompt_views.xml',
        'views/crm_lead_views.xml',
        'views/login_template.xml',
        'views/crm_pipeline_data.xml',
    ],
    'installable': True,
    'assets': {
        'web.assets_backend': [
            ('prepend', 'custom_crm_propify/static/src/scss/primary_variables.scss'),
            'custom_crm_propify/static/src/css/style.css',
            'custom_crm_propify/static/src/scss/kanban_style.scss',
        ],
        'web.assets_frontend': [
            'custom_crm_propify/static/src/css/login_style.css',
        ],
    },
    'application': True,
}