import { useState } from "react";

export const App = ({ apiUrl }) => {
  const [data, setData] = useState(null);
  console.log({ apiUrl });
  const fetchData = async () => {
    try {
      const response = await fetch(apiUrl);
      const jsonData = await response.json();
      setData(jsonData);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };
  return (
    <>
      <h1>Fetching from {apiUrl}</h1>
      <button onClick={fetchData}>Fetch Data</button>
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </>
  );
};
