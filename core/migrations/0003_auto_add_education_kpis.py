from django.db import migrations

def add_education_kpis(apps, schema_editor):
    Project = apps.get_model('core', 'Project')
    KPI = apps.get_model('core', 'Indicator')

    # Find Education project
    try:
        education = Project.objects.get(name="Education")
    except Project.DoesNotExist:
        return

    kpis = [
        "Number of Girls supported with university tuition fee",
        "Number of Boys supported with university tuition fee",
        "Number of Girls supported with university monthly upkeep allowance",
        "Number of Boys supported with university monthly upkeep allowance",
        "Number of Boys supported with school fees in secondary schools",
        "Number of Girls supported with school fees in secondary schools",
        "Number of girls supported with re-usable sanitary pads",
        "Number of Girls supported with school uniforms",
        "Number of Boys supported with school uniforms",
        "Number of Girls supported with writing materials and other stationeries",
        "Number of Boys supported with writing materials and other stationeries",
        "Number of Girls on bursary, dropping out of school",
        "Number of Boys on bursary, dropping out of school",
        "Number of Girls passing their end-of-term examinations",
        "Number of Boys passing their end-of-term examinations",
        "Number of Boys enrolled in vocational skills training",
        "Number of Girls enrolled in vocational skills training",
        "Number of schools reached with education services",
        "Number of boys graduating from the bursary scheme",
        "Number of girls graduating from the bursary scheme",
        "Number of Girls progressing to tertiary education after graduating from secondary",
        "Number of boys progressing to tertiary education after graduating from secondary",
        "Number of students accessing library services in primary schools",
        "Number of schools supported with school infrastructure",
        "Number of schools supported with desks",
        "Number of schools supported with sporting equipments",
        "Number of schools supported with study solar lamps",
    ]

    for kpi in kpis:
        KPI.objects.get_or_create(project=education, name=kpi)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_add_projects'),
    ]

    operations = [
        migrations.RunPython(add_education_kpis),
    ]
