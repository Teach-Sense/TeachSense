type Props = {
  score: number;
};

const ComprehensionCard = ({ score }: Props) => {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-xl font-bold mb-3">
        Student Comprehension
      </h2>

      <p className="text-5xl font-bold text-green-600">
        {score}%
      </p>
    </div>
  );
};

export default ComprehensionCard;