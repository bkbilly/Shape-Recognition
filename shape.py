import os
import sys
import random
import signal
import numpy as np
import matplotlib.pyplot as plt
from scipy import misc
import imageio
from neuralnet import *
from nnmath import *
from genetics import GeneticAlgorithm, GAKill
from tqdm import tqdm

def read_data(path):
	data = []
	for (dirpath, dirnames, filenames) in os.walk(path):
		for dirname in dirnames:
			for f in os.listdir(dirpath + dirname):
				try:
				    img = imageio.imread(dirpath + dirname + '/' + f, as_gray=True)
				    data.append((dirname, img))
				except Exception as e:
					print('error1:', e, f)
					pass
	return data

def main(argv):
	# Set Numpy warning level
	np.seterr(over='ignore')

	# Define target shapes
	targets = np.array(['rectangle', 'circle', 'triangle'])

	if argv[1] == 'train':
		# Check the input arguments
		if len(argv) < 5:
			print ("Usage: python shape.py train <GA-epochs> <SGD-epochs> <visFlag>")
			sys.exit()

		# Load the training data
		training_data = read_data('training_data/')
		test_data = read_data('test_data/')

		# Shuffle for more randomness
		random.shuffle(training_data)

		# Create a GA of neural nets
		img_len = len(training_data[0][1])
		ga = GeneticAlgorithm(epochs = int(argv[2]),
								mutation_rate = 0.01,
								data = training_data,
								targets = targets,
								obj = NeuralNet,
								args = [img_len, 10, 4, 3])

		# Create the 1st generation
		print ("Creating population...")
		ga.populate(200)

		print ("Initiating GA heuristic approach...")

		# Start evolution
		errors = []
		# while ga.evolve():
		pbar = tqdm(range(ga.armageddon))
		for i in pbar:
			try:
				ga.evaluate()
				ga.crossover()
				ga.epoch += 1

				# Store error
				errors.append(ga.error)
				# pbar.set_postfix({"error": ga.error})
				pbar.set_postfix_str(f"error: {ga.error}")
				# print(f"{ga.epoch}) error: {ga.error}")
			except GAKill as e:
				print('error2:', e.message)
				break

		vis = bool(int(argv[4]))
		if vis:
			# Plot error over time
			fig = plt.figure()
			plt.plot(range(ga.epoch), errors)
			plt.xlabel('Time (Epochs)')
			plt.ylabel('Error')
			plt.show()

		print ("--------------------------------------------------------------\n")

		nn = ga.fittest()
		epochs = int(argv[3])
		if epochs:
			print ("Initiating Gradient Descent optimization...")
			try:
				nn.gradient_descent(training_data, targets, epochs, test_data=test_data, vis=vis)
			except GAKill as e:
				print('error3:', e.message)

		nn.save("neuralnet.pkt")
		print ("Done!")

	elif argv[1] == "validate":
		test_data = read_data('test_data/')

		nn = NeuralNet([], build=False)
		nn.load("neuralnet.pkt")

		accuracy = nn.validate(targets, test_data)
		print ("Accuracy: " + str(accuracy))

	elif argv[1] == "predict":
		# Check the arguments
		if len(argv) < 3:
		    print ("Usage: python shape.py test <image>")
		    sys.exit()

		# Read the test image
		img = imageio.imread(argv[2], as_gray=True)

		# Build the neural net from file
		nn = NeuralNet([], build=False)
		nn.load("neuralnet.pkt")

		# Predict
		activations, zs = nn.feed_forward(img)
		print (targets[np.argmax(activations[-1])])

	else:
		print ("ERROR: Unknown command " + argv[1])


def signal_handler(signal, frame):
	raise(GAKill("\nAborting Search..."))

if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal_handler)
	main(sys.argv)
