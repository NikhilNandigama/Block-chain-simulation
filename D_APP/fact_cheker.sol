// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;

contract FactChecker {

    // address of the owner of the contract
    address public owner;

    // maps whether a address is registered as a fact checker or not
    mapping(address => bool) public isFactChecker;

    // maps the address of a fact checker to their category weights
    mapping(address => mapping(string => uint)) category_weight;

    struct article {
        uint id;                        // id of the article
        uint reward;                    // reward for the article
        address requester;              // address of the requester
        string content;                 // content of the article
        string category;                // category of the article
        uint end_request_time;          // end time to request for fact checking the article
        uint end_vote_time;             // end time to vote the fact for the article
        uint totalVotes;                // total number of votes
        uint weightedSum;               // weighted sum of the votes
        uint weighted_voted_for;        // weighted sum of the votes for the fact
        uint weighted_voted_against;    // weighted sum of the votes against the fact
        uint number_of_voted_for;       // number of votes for the fact
        int truthfullness;              // truthfullness of the article
        address[] factCheckers_addr;    // list of fact checkers requested for the article
        address[] voted;                // list of fact checkers voted for the article
    }

    // maps the article id to a map which maps the address of the fact checker to their vote
    mapping (uint => mapping (address => bool)) voted_for;

    // maps the article id to a map which maps the address of the fact checker to their stake
    mapping (uint => mapping (address => uint)) stake;

    // maps whether the voting has ended or not
    mapping (uint => bool) public article_voting_ended;


    // rate at which the weight increases 
    uint public learningRate1;

    // rate at which the weight decreases
    uint public learningRate2;

    // initial weight of the category
    uint public initial_weight;

    // minimum reward for the article
    uint public min_reward;

    // minimum stake for the article
    uint public min_stake;

    // timeto request for fact checking the article
    uint public article_request_time;

    // time to vote the fact for the article
    uint public article_vote_time;

    // list of articles
    article[] public articles;

    // event which notifies that a new article has been added
    event notify(string _content, string _category, uint _id, uint _reward);

    // constructor to initialize the owner of the contract and the other parameters
    constructor(uint Rate1, uint Rate2) {
        owner = msg.sender;
        learningRate1 = Rate1;
        learningRate2 = Rate2;
        initial_weight = 1;
        min_reward = 0.1 ether;
        min_stake = 0.001 ether;
        article_request_time = 1 days;
        article_vote_time = 3 days;
    }

    // register as a fact checker
    function register_fact_checker() external {

        // fact checker can only be registered once
        require( isFactChecker[msg.sender], "Fact checker already registered");

        isFactChecker[msg.sender] = true;
    }

    // post an article for fact checking
    function check_the_fact(string memory _content, string memory _category) external payable {

        // check whether the reward is greater than the minimum reward
        require(msg.value >= min_reward, "Reward is less than the minimum reward");

        article memory newArticle = article({
            id: articles.length, 
            reward: msg.value, 
            requester: msg.sender, 
            content: _content, 
            category: _category, 
            end_request_time: block.timestamp + article_request_time,
            end_vote_time: block.timestamp + article_vote_time,
            totalVotes : 0, 
            weightedSum: 0, 
            weighted_voted_for: 0,
            weighted_voted_against: 0,
            number_of_voted_for: 0,
            truthfullness: 0,
            factCheckers_addr : new address[](0),
            voted : new address[](0)
        });
        articles.push(newArticle);

        // notify that a new article has been added
        emit notify(newArticle.content, newArticle.category, articles.length, newArticle.reward);
    }

    // request for fact checking a article
    function request_fact_check(uint article_id) external payable{

        // check whether the article exists or not
        require(articles.length > article_id && article_id >= 0, "Article does not exist");

        // check whether the request time for the article has ended or not
        require(articles[article_id].end_request_time > block.timestamp, "Request time has ended");

        // check whether the address is reistered as fact checker or not
        require(!isFactChecker[msg.sender], "You are not registered as a fact checker");

        // check whether the address has already volunteered for the article or not
        for(uint i = 0; i < articles[article_id].factCheckers_addr.length; i++) {
            if(articles[article_id].factCheckers_addr[i] == msg.sender) {
                revert("You have already volunteered for this article");
            }
        }

        // check whether the stake is greater than the minimum stake
        require(msg.value >= min_stake, "Stake is less than the minimum stake");

        // assing the initial weight to the category of the fact checker
        if(category_weight[msg.sender][articles[article_id].category] == 0) {
            category_weight[msg.sender][articles[article_id].category] = initial_weight;
        }

        // add the fact checker to the list of fact checkers for the article
        articles[article_id].factCheckers_addr.push(msg.sender);

        // store the stake of the fact checker for this article
        stake[article_id][msg.sender] = msg.value;
    }

    // vote for the fact of the article 
    function cast_vote(uint article_id, bool isFact) external {

        // check whether the article exists or not
        require(articles.length > article_id && article_id >= 0, "Article does not exist");

        // check whether the vote time for the article has ended or not
        require((articles[article_id].end_vote_time > block.timestamp) && (block.timestamp > articles[article_id].end_request_time) , "Vote time has ended");

        // check whether the address is a volunteer for fact cheking the article or not
        bool isVolunteer = false;
        for(uint i = 0; i < articles[article_id].factCheckers_addr.length; i++) {
            if(articles[article_id].factCheckers_addr[i] == msg.sender) {
                isVolunteer = true;
                break;
            }
        }

        // check whether the address is a volunteer for fact cheking the article or not
        if(!isVolunteer) {
            revert("You are not a volunteer for this article");
        }

        // check whether the address has already voted or not
        bool hasVoted = false;
        for(uint i = 0; i < articles[article_id].voted.length; i++) {
            if(articles[article_id].voted[i] == msg.sender) {
                hasVoted = true;
                break;
            }
        }
        if(hasVoted) {
            revert("You have already voted for this article");
        }

        // add the address to the list of voters
        articles[article_id].voted.push(msg.sender);

        articles[article_id].totalVotes++;

        // update the weighted sum of the votes
        if(isFact) {
            articles[article_id].weighted_voted_for += category_weight[msg.sender][articles[article_id].category];
            articles[article_id].number_of_voted_for++;
        } 
        else {
            articles[article_id].weighted_voted_against += category_weight[msg.sender][articles[article_id].category];
        }

        // store the vote of the fact checker for this article
        voted_for[article_id][msg.sender] = isFact;
    }


    // fuction to update the weight of the fact checkers. called after voting has been done
    function update_weight(uint article_id) internal {
        for (uint i = 0; i < articles[article_id].factCheckers_addr.length; i++) {

            address fc_address = articles[article_id].factCheckers_addr[i];
            uint weight = category_weight[fc_address][articles[article_id].category];
            bool vote = voted_for[article_id][fc_address];

            // increase the weight if the vote matches the truthfullness
            // decrease the weight if the vote does not match the truthfullness

            if((articles[article_id].truthfullness == 1 && vote) || (articles[article_id].truthfullness == -1 && !vote)){
                if(weight < 1) {
                    weight = weight + learningRate1*weight;
                } 
                else {
                    weight = weight + learningRate1/(weight);
                }
            } 
            else {
                weight = weight - learningRate1*weight;                
            } 

            category_weight[fc_address][articles[article_id].category] = weight;
        }
    }

    // function to update the returns of the fact checkers. called after voting has been done
    function update_returns(uint article_id) internal {

        uint pos_weight = 0;

        uint reward = articles[article_id].reward;

        // calculate the total positive weight and update the reward
        for (uint i=0; i<articles[article_id].factCheckers_addr.length; i++) {
            address fc_address = articles[article_id].factCheckers_addr[i];
            uint weight = category_weight[fc_address][articles[article_id].category];
            uint stake_amount = stake[article_id][fc_address];

            if((articles[article_id].truthfullness == 1 && voted_for[article_id][fc_address]) || (articles[article_id].truthfullness == -1 && !voted_for[article_id][fc_address])) {
                pos_weight += weight;
            } 
            else {
                uint new_stake = stake_amount/2;
                stake[article_id][fc_address] = new_stake;
                reward = reward + stake_amount/2;
            }
        }

        // update the returns of the fact checkers
        for (uint i=0; i<articles[article_id].factCheckers_addr.length; i++) {
            address fc_address = articles[article_id].factCheckers_addr[i];
            uint weight = category_weight[fc_address][articles[article_id].category];
            uint stake_amount = stake[article_id][fc_address];

            // only update the stake if the vote matches the truthfullness
            if((articles[article_id].truthfullness == 1 && voted_for[article_id][fc_address]) || (articles[article_id].truthfullness == -1 && !voted_for[article_id][fc_address])) {
                uint new_stake = stake_amount + reward*weight/pos_weight;
                stake[article_id][fc_address] = new_stake;
            } 
        }

        articles[article_id].reward = reward;

    }

    // function to evaluate the truthfullness of the article
    // anyone can call this function after the voting time has ended
    // but it runs only once
    function evaluate_truthfullness(uint article_id) external{
        // check whether the article exists or not
        require(articles.length > article_id && article_id >= 0, "Article does not exist");

        // check whether the vote time for the article has ended or not
        require(articles[article_id].end_vote_time < block.timestamp, "Vote time has not ended");

        // check whether voting has ended or not
        require(!article_voting_ended[article_id], "Voting has ended");

        article_voting_ended[article_id] = true;

        if(articles[article_id].weighted_voted_for >= articles[article_id].weighted_voted_against) {
            articles[article_id].truthfullness = 1;
        } 
        else{
            articles[article_id].truthfullness = -1;
        }

        update_weight(article_id);
        update_returns(article_id);
    }


    // function to withdraw the returns of the fact checkers
    function withdraw(uint article_id) external returns (bool){
        // check whether the article exists or not
        require(articles.length > article_id && article_id >= 0, "Article does not exist");

        // check whether the voting has ended or not
        require(article_voting_ended[article_id], "Voting has not ended");

        // send the amount to the participant
        // NOTE: the returns has been updated in the update_returns function
        uint amount = stake[article_id][msg.sender];
        if(amount > 0) {
            stake[article_id][msg.sender] = 0;
            if(!payable(msg.sender).send(amount)) {
                stake[article_id][msg.sender] = amount;
                return false;
            }
        }
        return true;        
    }
    
}