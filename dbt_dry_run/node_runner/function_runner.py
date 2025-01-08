from dbt_dry_run.exception import UpstreamFailedException
from dbt_dry_run.literals import insert_dependant_sql_literals
from dbt_dry_run.models.manifest import Node
from dbt_dry_run.node_runner import NodeRunner
from dbt_dry_run.results import DryRunResult, DryRunStatus


class FunctionRunner(NodeRunner):
    """
    Function 是 Migo 自行開發的 materialized type，用來建立 BQ 的 UDF function
    """

    def _modify_sql(self, node: Node, sql_statement: str) -> str:
        params = node.config.params
        params_str = ", ".join(params) if params else ""
        sql_statement = f"CREATE OR REPLACE FUNCTION `{node.database}`.`{node.db_schema}`.`{node.alias}`({params_str}) RETURNS {node.config.return_type} AS (\n{sql_statement}\n)"
        if node.config.sql_header:
            sql_statement = f"{node.config.sql_header}\n{sql_statement}"
        return sql_statement

    def run(self, node: Node) -> DryRunResult:
        try:
            run_sql = insert_dependant_sql_literals(node, self._results)
        except UpstreamFailedException as e:
            return DryRunResult(node, None, DryRunStatus.FAILURE, e)

        run_sql = self._modify_sql(node, run_sql)
        status, model_schema, exception = self._sql_runner.query(run_sql)

        result = DryRunResult(node, model_schema, status, exception)
        return result
