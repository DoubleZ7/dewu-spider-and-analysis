from app.data_analysis.analysis_executor import AnalysisExecutor
from app.data_analysis.analysis import Analysis
from app.data_analysis.generate_reports import GenerateReports
from app.decorator.decorator import error_repeat


# an = AnalysisExecutor()
# an.update_one_month("EG6860")
# an.update_three_month("EG6860")
# an.reports_one_month("854262-001")
# an.reports_one_month("415445-101")
# an.reports_three_month("EG6860")

@error_repeat
def demo(dd):
    print(dd)
    a = 100 / 0


demo("sadsadsa")





