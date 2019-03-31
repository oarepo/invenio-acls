#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""name on actors."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2cd83b6065cc'
down_revision = '06aae02f41ca'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('explicit_acls_actor', sa.Column('name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    """Downgrade database."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('explicit_acls_actor', 'name')
    # ### end Alembic commands ###