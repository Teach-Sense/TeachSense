type Props = {
  transcript: string;
};

const TranscriptCard = ({ transcript }: Props) => {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-2xl font-bold mb-4">
        Full Transcript
      </h2>

      <p className="text-gray-700 leading-7 whitespace-pre-line">
        {transcript}
      </p>
    </div>
  );
};

export default TranscriptCard;