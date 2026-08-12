import AmbientCore from "@/components/AmbientCore";
import GuardianScannerForm from "@/components/GuardianScannerForm";
import LogoutButton from "@/components/LogoutButton";
import PageHeader from "@/components/PageHeader";

export default function GuardianScannerPage() {
  return (
    <main className="relative flex min-h-screen flex-col items-center gap-8 px-6 py-16">
      <AmbientCore />
      <LogoutButton />
      <PageHeader
        eyebrow="Tool 02"
        title="Guardian Scam Scanner"
        description="Paste any text — a message, link, or offer — to get a scam/phishing risk assessment with reasoning."
      />
      <GuardianScannerForm />
    </main>
  );
}
