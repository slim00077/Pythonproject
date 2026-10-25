"""
Backend MySQL adapté au service MariaDB livré avec XAMPP.

XAMPP (toutes les versions 8.x à ce jour) embarque MariaDB 10.4, alors que
Django 5.2 exige MariaDB 10.5 ou plus récent et refuse donc de se connecter
(``NotSupportedError: MariaDB 10.5 or later is required``).

Ce backend n'abaisse QUE ce plancher de version ; tout le reste (SQL, types de
colonnes, transactions, contraintes) est le backend MySQL standard de Django.

À n'utiliser qu'en développement local, le temps de la démonstration. En
production, ou dès que possible en local, mettez MariaDB à niveau (10.11 LTS)
et repassez sur ``DB_ENGINE=mysql``, qui utilise le backend Django d'origine.
"""

import operator

from django.db.backends.mysql import base
from django.db.backends.mysql.features import DatabaseFeatures as MySQLFeatures
from django.utils.functional import cached_property


class DatabaseFeatures(MySQLFeatures):
    """Ramène le plancher MariaDB de 10.5 à 10.4 (version fournie par XAMPP)."""

    @cached_property
    def minimum_database_version(self):
        if self.connection.mysql_is_mariadb:
            return (10, 4)
        return super().minimum_database_version

    @cached_property
    def can_return_columns_from_insert(self):
        # Django 5.2 suppose « INSERT ... RETURNING » disponible sur toute
        # MariaDB, car son minimum est 10.5 ; la clause n'existe en réalité
        # qu'à partir de 10.5. On rétablit donc la condition de version
        # utilisée par Django 4.2.
        if self.connection.mysql_is_mariadb:
            return self.connection.mysql_version >= (10, 5)
        return super().can_return_columns_from_insert

    can_return_rows_from_bulk_insert = property(
        operator.attrgetter('can_return_columns_from_insert')
    )


class DatabaseWrapper(base.DatabaseWrapper):
    features_class = DatabaseFeatures
