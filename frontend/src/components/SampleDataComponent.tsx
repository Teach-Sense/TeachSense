import { useEffect, useState } from "react";
import { healthAPI } from "../services/api";

const SampleDataComponent = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    healthAPI.check()
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Error fetching data");
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Backend Health Status</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};

export default SampleDataComponent;