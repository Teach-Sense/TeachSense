type Props = {
  question: string;
  answer: string;
};

const QuestionCard = ({
  question,
  answer,
}: Props) => {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h3 className="text-lg font-bold mb-3">
        {question}
      </h3>

      <p className="text-gray-700">
        <span className="font-semibold">
          Answer:
        </span>{" "}
        {answer}
      </p>
    </div>
  );
};

export default QuestionCard;