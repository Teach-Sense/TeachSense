import React, { useEffect, useState } from 'react';
import { fetchSampleData } from '../services/api';

const SampleDataComponent: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSampleData()
      .then((res: any) => {
        setData(res);
        setLoading(false);
      })
      .catch((err: any) => {
        setError(err.message || 'Error fetching data');
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Sample Data from Backend</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};

export default SampleDataComponent;
