type Props = {
  summary: string;
};

const SummaryCard = ({ summary }: Props) => {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-2xl font-bold mb-4">
        Lecture Summary
      </h2>

      <p className="text-gray-700 leading-7">
        {summary}
      </p>
    </div>
  );
};

export default SummaryCard;