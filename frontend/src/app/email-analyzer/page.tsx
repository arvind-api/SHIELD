import AmbientCore from "@/components/AmbientCore";
import EmailAnalyzerForm from "@/components/EmailAnalyzerForm";
import LogoutButton from "@/components/LogoutButton";
import PageHeader from "@/components/PageHeader";

export default function EmailAnalyzerPage() {
  return (
    <main className="relative flex min-h-screen flex-col items-center gap-8 px-6 py-16">
      <AmbientCore />
      <LogoutButton />
      <PageHeader
        eyebrow="Tool 01"
        title="Email Analyzer"
        description="Paste or upload an email to get tone/intent analysis, phishing signals, and a reply suggestion."
      />
      <EmailAnalyzerForm />
    </main>
  );
}
