from app.data_analysis.analysis_executor import AnalysisExecutor
from app.data_analysis.analysis import Analysis


# an = AnalysisExecutor()
# an.update_one_date("GU8591-104")
an = Analysis("CV8480-300")
an.get_user_repeat()

