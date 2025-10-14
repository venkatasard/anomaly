import "./globals.css";
import {Shell} from "@/components/shell";
export const metadata={title:"Anomaly | Operations Intelligence",description:"AI-powered telemetry and incident investigation"};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en" className="dark"><body><Shell>{children}</Shell></body></html>}
