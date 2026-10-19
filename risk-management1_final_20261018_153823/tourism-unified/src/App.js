import React, { useState } from "react";
import Navbar from "./Navbar";
import Home from "./pages/Home";
import Discover from "./pages/tourist/Discover";
import DestinationDetail from "./pages/tourist/DestinationDetail";
import { ThemeProvider } from "./design/ThemeContext";

function AppInner() {
  const [page, setPage] = useState("home");
  const [selectedSite, setSelectedSite] = useState(null);

  const handleNavigate = (target) => {
    setPage(target);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const renderPage = () => {
    switch (page) {
      case "home":
        return <Home onGetStarted={() => handleNavigate("discover")} />;

      case "discover":
        return (
          <Discover
            onSelectSite={(id, date) => {
              setSelectedSite({ id, date });
              setPage("destinationDetail");
            }}
          />
        );

      case "destinationDetail":
        return (
          <DestinationDetail
            siteId={selectedSite ? selectedSite.id : null}
            date={selectedSite ? selectedSite.date : null}
            onSelectSite={(id, d) => {
              setSelectedSite({ id, date: d });
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            onBack={() => setPage("discover")}
          />
        );

      default:
        return null;
    }
  };

  return (
    <>
      <Navbar active={page} onNavigate={handleNavigate} />
      {renderPage()}
    </>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AppInner />
    </ThemeProvider>
  );
}