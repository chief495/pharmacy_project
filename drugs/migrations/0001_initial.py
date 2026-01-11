# Generated manually - CustomUser must be created first

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Create CustomUser first
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Электронная почта')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='Имя')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='Фамилия')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Сотрудник')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата регистрации')),
                ('email_notifications', models.BooleanField(default=True, verbose_name='Email уведомления')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
                'db_table': 'custom_user',
            },
        ),
        # Now create other models
        migrations.CreateModel(
            name='Drug',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mnn', models.CharField(max_length=255, verbose_name='МНН (Международное название)')),
                ('trade_name', models.CharField(max_length=255, verbose_name='Торговое название')),
                ('form', models.CharField(max_length=100, verbose_name='Форма выпуска')),
                ('dosage', models.CharField(max_length=100, verbose_name='Дозировка')),
                ('manufacturer', models.CharField(max_length=255, verbose_name='Производитель')),
                ('atx_code', models.CharField(blank=True, max_length=20, null=True, verbose_name='АТХ код')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Препарат',
                'verbose_name_plural': 'Препараты',
                'ordering': ['trade_name'],
            },
        ),
        migrations.CreateModel(
            name='PharmacyNetwork',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название сети')),
                ('website', models.URLField(blank=True, null=True, verbose_name='Сайт')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Телефон')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
            ],
            options={
                'verbose_name': 'Аптечная сеть',
                'verbose_name_plural': 'Аптечные сети',
            },
        ),
        migrations.CreateModel(
            name='Pharmacy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название аптеки')),
                ('address', models.TextField(verbose_name='Адрес')),
                ('city', models.CharField(max_length=100, verbose_name='Город')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Телефон')),
                ('latitude', models.FloatField(blank=True, null=True, verbose_name='Широта')),
                ('longitude', models.FloatField(blank=True, null=True, verbose_name='Долгота')),
                ('working_hours', models.CharField(blank=True, max_length=100, null=True, verbose_name='Часы работы')),
                ('network', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drugs.pharmacynetwork', verbose_name='Сеть')),
            ],
            options={
                'verbose_name': 'Аптека',
                'verbose_name_plural': 'Аптеки',
            },
        ),
        migrations.CreateModel(
            name='Availability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена')),
                ('quantity', models.IntegerField(default=0, verbose_name='Количество')),
                ('last_updated', models.DateTimeField(auto_now=True, verbose_name='Последнее обновление')),
                ('is_available', models.BooleanField(default=True, verbose_name='В наличии')),
                ('drug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drugs.drug', verbose_name='Препарат')),
                ('pharmacy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drugs.pharmacy', verbose_name='Аптека')),
            ],
            options={
                'verbose_name': 'Наличие препарата',
                'verbose_name_plural': 'Наличие препаратов',
                'unique_together': {('drug', 'pharmacy')},
            },
        ),
        migrations.CreateModel(
            name='Analogue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('similarity_score', models.FloatField(default=0.0, verbose_name='Коэффициент схожести')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('analogue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analogue_drug', to='drugs.drug', verbose_name='Аналог')),
                ('original', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='original_drug', to='drugs.drug', verbose_name='Оригинальный препарат')),
            ],
            options={
                'verbose_name': 'Аналог препарата',
                'verbose_name_plural': 'Аналоги препаратов',
                'unique_together': {('original', 'analogue')},
            },
        ),
        migrations.CreateModel(
            name='PriceHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена')),
                ('recorded_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')),
                ('availability', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drugs.availability', verbose_name='Наличие')),
            ],
            options={
                'verbose_name': 'История цены',
                'verbose_name_plural': 'История цен',
                'ordering': ['-recorded_at'],
            },
        ),
        migrations.CreateModel(
            name='UserSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(blank=True, max_length=100, null=True, verbose_name='Город')),
                ('max_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Максимальная цена')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('drug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drugs.drug', verbose_name='Препарат')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Подписка пользователя',
                'verbose_name_plural': 'Подписки пользователей',
                'unique_together': {('user', 'drug', 'city')},
            },
        ),
    ]
