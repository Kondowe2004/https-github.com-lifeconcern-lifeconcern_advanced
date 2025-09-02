from django.db import migrations

def add_projects(apps, schema_editor):
    Project = apps.get_model('core', 'Project')
    projects = [
        "Education",
        "HIV",
        "SRHR",
        "Entrepreneurship",
        "Human Rights",
        "Climate Change",
    ]
    for name in projects:
        Project.objects.get_or_create(name=name)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_projects),
    ]
