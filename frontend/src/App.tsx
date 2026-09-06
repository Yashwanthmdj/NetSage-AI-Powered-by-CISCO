import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { CaseDetailPage } from "./pages/CaseDetailPage";
import { CasesPage } from "./pages/CasesPage";
import { CommandCenterPage } from "./pages/CommandCenterPage";
import { DiagnosisPage } from "./pages/DiagnosisPage";
import { RaiLogPage } from "./pages/RaiLogPage";
import { ReviewQueuePage } from "./pages/ReviewQueuePage";
import { ReviewWorkspacePage } from "./pages/ReviewWorkspacePage";
import { RuleEnginePage } from "./pages/RuleEnginePage";
import { TroubleshootPage } from "./pages/TroubleshootPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<CommandCenterPage />} />
        <Route path="/troubleshoot" element={<TroubleshootPage />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/cases/:caseCode" element={<CaseDetailPage />} />
        <Route path="/diagnosis" element={<DiagnosisPage />} />
        <Route path="/review" element={<ReviewQueuePage />} />
        <Route path="/review/:caseCode" element={<ReviewWorkspacePage />} />
        <Route path="/rules" element={<RuleEnginePage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/rai" element={<RaiLogPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
