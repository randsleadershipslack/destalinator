## Introduction

Alongside with reaping stale channels, Destalinator runs a flagging service
that copies some of the messages from the last day into a summary channel.

## Source Code

The flagging service runs based on source code in flagger.py

## Configuration

For its configuration, the flagging service looks for messages in a
configuration channel; the name of the configuration channel is set in
configuration.yaml (by default, #zmeta-control)

## Configuration messages

Flagger sweeps the configuration channel for messages of the form

`flag content rule NAMEOFRULE COMPARATORINTEGER :REACTION: #CHANNELNAME`

Where
"flag content rule" is literal

NAMEOFRULE is a label for the rule

COMPARATORINTEGER is a combination of a COMPARATOR and an INTEGER.

COMPARATOR is one of '>', '<', '==', '>=', or '<='

INTEGER is ... well ... an integer

REACTION is an emoji REACTION

CHANNELNAME is the name of an existing channel.

So for example
`flag content rule piccard >=1 :piccard: #zmeta-piccard`

Would find all messages in the last day that have at least one :piccard: emoji
reaction and repost them to the #zmeta-piccard channel

## Changing rules

The flagger will use the latest definition of a rule (based on the rule name);
this allows redefining rules by simply sending a new rule definition with the
name of an existing rule

## Deleting rules

`flag content rule NAME delete`

Will delete the content rule with the given name
