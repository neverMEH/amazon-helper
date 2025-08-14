import { useParams } from 'react-router-dom';

export default function DataSourceDetailTest() {
  const { schemaId } = useParams<{ schemaId: string }>();
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Data Source Detail Test</h1>
      <p>Schema ID from URL: {schemaId}</p>
      <p>This is a test component to verify routing works.</p>
    </div>
  );
}