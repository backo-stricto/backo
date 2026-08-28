"""
Module providing the migration
"""

# pylint: disable=wrong-import-position, no-member, import-error, protected-access, wrong-import-order, attribute-defined-outside-init

# Importing module
import sys

# used for developpement
sys.path.insert(1, "../../stricto")

from stricto import (
    validation_parameters,
    Dict,
    String,
    Int,
    List,
    Bool,
    FreeDict,
)


class MigrationReport(Dict):  # pylint: disable=too-many-instance-attributes
    """The migration report"""

    @validation_parameters
    def __init__(self, **kwargs):
        """
        Constructor
        """

        super().__init__(
            {
                "db_compliant": Bool(),
                "alter_db_message": String(),
                "": Dict({"_ids": List(String(), default=[]), "total": Int(default=0)}),
                "no_changes": Dict(
                    {"_ids": List(String(), default=[]), "total": Int(default=0)}
                ),
                "changes": Dict(
                    {
                        "_ids": List(String(), default=[]),
                        "diff": List(FreeDict(), default=[]),
                        "total": Int(default=0),
                    }
                ),
            },
            **kwargs,
        )

    def add_check_model(self, db_compliant: bool, alter_db_message: str) -> None:
        """
        Add the message from DBHandler.check_structure()

        :param db_compliant: True if the DB is OK, or False if you must alter tables or similar
        :type db_compliant: bool
        :param alter_db_message: the commands to run
        :type alter_db_message: str
        """
        self.db_compliant = db_compliant
        self.alter_db_message = alter_db_message

    def add_change(self, _id: str, diff: dict) -> None:
        """Add a changement into the report

        :param _id: _description_the _id concerning with the changement
        :type _id: str
        :param change: the changement as a deepdiff object
        :type change: dict
        """
        self.changes._ids.append(_id)
        self.changes.diff.append(diff)
        self.changes.total = len(self.changes._ids)

    def add_no_change(self, _id: str) -> None:
        """Add a _id without changement into the report

        :param _id: _description_the _id concerning with the changement
        :type _id: str
        """
        self.no_changes._ids.append(_id)
        self.no_changes.total = len(self.no_changes._ids)
