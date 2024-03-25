# The Set Covering Problem with Conflicts on Sets (SCP-CS)

This source code is provided as an attachment to the article [Solving the Set Covering Problem with Conflicts on Sets: A new parallel GRASP](https://doi.org/10.1016/j.cor.2024.106620) by Francesco Carrabs, Raffaele Cerulli, Renata Mansini, Lorenzo Moreschini[^1] and Domenico Serra.

## Documentation

For more information on how to use this software refer to the documentation files inside the `docs/` folder.
 - [docs/howto.md](docs/howto.md): provides usage instructions and examples
 - [docs/input.md](docs/input.md): provides information about the data set files
 - [docs/output.md](docs/output.md): provides information about the output files

## Experimental results

The set of files containing the experimental results presented in the paper can be found in the [results][0] folder and can be downloaded in a [zip archive][1].

## How to cite

```bibtex
@article{CARRABS2024106620,
    title = {Solving the Set Covering Problem with Conflicts on Sets: A new parallel GRASP},
    journal = {Computers & Operations Research},
    volume = {166},
    pages = {106620},
    year = {2024},
    issn = {0305-0548},
    doi = {https://doi.org/10.1016/j.cor.2024.106620},
    url = {https://www.sciencedirect.com/science/article/pii/S0305054824000923},
    author = {Francesco Carrabs and Raffaele Cerulli and Renata Mansini and Lorenzo Moreschini and Domenico Serra},
    keywords = {Heuristics, Set Covering Problem, Conflicts, GRASP, Parallel algorithm},
    abstract = {In this paper, we analyze a new variant of the well-known NP-hard Set Covering Problem, characterized by pairwise conflicts among subsets of items. Two subsets in conflict can belong to a solution provided that a positive penalty is paid. The problem looks for the optimal collection of subsets representing a cover and minimizing the sum of covering and penalty costs. We introduce two integer linear programming formulations and a quadratic one for the problem and provide a parallel GRASP (Greedy Randomized Adaptive Search Procedure) that, during parallel executions of the same basic procedure, shares information among threads. We tailor such a parallel processing to address the specific problem in an innovative way that allows us to prevent redundant computations in different threads, ultimately saving time. To evaluate the performance of our algorithm, we conduct extensive experiments on a large set of new instances obtained by adapting existing instances for the Set Covering Problem. Computational results show that the proposed approach is extremely effective and efficient providing better results than Gurobi (tackling three alternative mathematical formulations of the problem) in less than 1/6 of the computational time.}
}
```


  [^1]: Corresponding author, contact him at <lorenzo.moreschini@unibs.it>.

  [0]: <results/> "Results folder"
  [1]: <results/results.zip> "Results archive"
