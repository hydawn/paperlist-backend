# Generated by Django 5.0.4 on 2024-05-29 13:10

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaperTags',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag_name', models.CharField(max_length=128)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Paper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=4096)),
                ('abstract', models.CharField(max_length=131072)),
                ('file_name', models.CharField(max_length=1024)),
                ('file_content', models.FileField(upload_to='objects/')),
                ('publication_date', models.DateField()),
                ('journal', models.CharField(max_length=1024)),
                ('total_citations', models.IntegerField(validators=[django.core.validators.MinValueValidator(0, message='citations must be at least 0')])),
                ('private', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaperByScholar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scholar', models.CharField(max_length=256)),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.paper')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaperCited',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cite_paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cites', to='api.paper')),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cited_by', to='api.paper')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaperSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=512)),
                ('description', models.CharField(max_length=4096, null=True)),
                ('private', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaperSetContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.paper')),
                ('paper_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.paperset')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaperStarComments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stars', models.IntegerField(validators=[django.core.validators.MinValueValidator(1, message='stars must be at least 1'), django.core.validators.MaxValueValidator(5, message='stars cannot be more than 5')])),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.paper')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaperSetWithTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.paper')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.papertags')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaperTextComments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(max_length=4096)),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.paper')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaperWithTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.paper')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.papertags')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]