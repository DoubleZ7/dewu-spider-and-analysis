from app.data_analysis.analysis_executor import AnalysisExecutor
from app.data_analysis.analysis import Analysis
from app.data_analysis.generate_reports import GenerateReports
from app.decorator.decorator import error_repeat


an = AnalysisExecutor()
an.update_one_month("327624-001")
# an.update_three_month("327624-001")
# an.reports_one_month("327624-001")
# an.reports_three_month("327624-001")





