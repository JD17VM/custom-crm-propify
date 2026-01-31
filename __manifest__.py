{
    'name': 'Custom CRM PROPIFY PRO',
    'version': '1.0',
    'depends': ['base', 'crm', 'web'],
    'data': [
        'views/crm_views.xml',
    ],
    'installable': True,
    'assets': {
        'web.assets_backend': [
            ('prepend', 'crm_custom_fields/static/src/scss/primary_variables.scss'),
        ],
    },
    'application': True,
}